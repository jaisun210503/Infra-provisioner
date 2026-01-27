import os
import sys
import subprocess
import json
import logging
import shutil
import secrets
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from celery_app import celery_app
from database import SessionLocal
from models import ResourceRequest

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERRAFORM_MODULES_PATH = os.path.join(BASE_DIR, "terraform", "modules")
TERRAFORM_WORKSPACES_PATH = os.path.join(BASE_DIR, "terraform", "workspaces")

DRY_RUN_MODE = True


@celery_app.task(bind=True, max_retries=3)
def provision_resource(self, request_id: int):
    db = SessionLocal()

    try:
        request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()

        if not request:
            logger.error(f"Request {request_id} not found")
            return {"status": "error", "message": "Request not found"}

        if request.status != "approved":
            logger.warning(f"Request {request_id} is not approved, skipping")
            return {"status": "skipped", "message": "Request not approved"}

        logger.info(f"Starting provisioning for request {request_id}: {request.resource_type}")

        request.status = "provisioning"
        db.commit()

        result = _provision_by_type(request)

        if result["success"]:
            request.status = "provisioned"
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioned successfully:\n{result.get('output', '')}"
        else:
            request.status = "failed"
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioning failed:\n{result.get('error', '')}"

        db.commit()

        logger.info(f"Provisioning complete for request {request_id}: {request.status}")
        return {"status": request.status, "request_id": request_id}

    except Exception as e:
        logger.error(f"Error provisioning request {request_id}: {str(e)}")

        try:
            request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
            if request:
                request.status = "failed"
                request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioning error: {str(e)}"
                db.commit()
        except:
            pass

        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


def _provision_by_type(request: ResourceRequest) -> dict:
    resource_type = request.resource_type
    config = request.config or {}
    name = request.name

    logger.info(f"Provisioning {resource_type}: {name} with config: {config}")

    if resource_type == "database":
        return _provision_database(request)
    elif resource_type == "s3":
        return _provision_s3(request)
    elif resource_type == "k8s_namespace":
        return _provision_k8s_namespace(request)
    else:
        return {"success": False, "error": f"Unknown resource type: {resource_type}"}


def _generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _create_workspace(request_id: int, resource_type: str) -> str:
    workspace_dir = os.path.join(TERRAFORM_WORKSPACES_PATH, f"request-{request_id}")
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir


def _write_provider_config(workspace_dir: str, provider: str):
    if provider == "aws":
        provider_tf = '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}
'''
    elif provider == "kubernetes":
        provider_tf = '''
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

variable "kubeconfig_path" {
  type    = string
  default = "~/.kube/config"
}
'''
    else:
        provider_tf = ""

    with open(os.path.join(workspace_dir, "provider.tf"), "w") as f:
        f.write(provider_tf)


def _provision_database(request: ResourceRequest) -> dict:
    config = request.config or {}
    workspace_dir = _create_workspace(request.id, "database")

    _write_provider_config(workspace_dir, "aws")

    engine = config.get("engine", "postgres")
    size = config.get("size", "small")

    size_mapping = {
        "small": "db.t3.micro",
        "medium": "db.t3.small",
        "large": "db.t3.medium",
        "xlarge": "db.t3.large"
    }

    engine_versions = {
        "postgres": "15.4",
        "mysql": "8.0",
        "mariadb": "10.6"
    }

    main_tf = f'''
module "database" {{
  source = "{TERRAFORM_MODULES_PATH}/database"

  name             = var.name
  engine           = var.engine
  engine_version   = var.engine_version
  instance_class   = var.instance_class
  db_name          = var.db_name
  username         = var.username
  password         = var.password
  request_id       = var.request_id
  team_id          = var.team_id
}}

output "endpoint" {{
  value = module.database.endpoint
}}

output "address" {{
  value = module.database.address
}}

output "port" {{
  value = module.database.port
}}
'''

    tfvars = f'''
name           = "{request.name}"
engine         = "{engine}"
engine_version = "{engine_versions.get(engine, '15.4')}"
instance_class = "{size_mapping.get(size, 'db.t3.micro')}"
db_name        = "{config.get('db_name', 'appdb')}"
username       = "{config.get('username', 'admin')}"
password       = "{config.get('password', _generate_password())}"
request_id     = "{request.id}"
team_id        = "{request.team_id}"
aws_region     = "{config.get('region', 'us-east-1')}"
'''

    with open(os.path.join(workspace_dir, "main.tf"), "w") as f:
        f.write(main_tf)

    with open(os.path.join(workspace_dir, "terraform.tfvars"), "w") as f:
        f.write(tfvars)

    return _run_terraform_workflow(workspace_dir)


def _provision_s3(request: ResourceRequest) -> dict:
    config = request.config or {}
    workspace_dir = _create_workspace(request.id, "s3")

    _write_provider_config(workspace_dir, "aws")

    main_tf = f'''
module "s3" {{
  source = "{TERRAFORM_MODULES_PATH}/s3"

  name       = var.name
  public     = var.public
  request_id = var.request_id
  team_id    = var.team_id
}}

output "bucket_name" {{
  value = module.s3.bucket_name
}}

output "bucket_arn" {{
  value = module.s3.bucket_arn
}}

output "bucket_domain_name" {{
  value = module.s3.bucket_domain_name
}}
'''

    tfvars = f'''
name       = "{request.name}"
public     = {str(config.get('public', False)).lower()}
request_id = "{request.id}"
team_id    = "{request.team_id}"
aws_region = "{config.get('region', 'us-east-1')}"
'''

    with open(os.path.join(workspace_dir, "main.tf"), "w") as f:
        f.write(main_tf)

    with open(os.path.join(workspace_dir, "terraform.tfvars"), "w") as f:
        f.write(tfvars)

    return _run_terraform_workflow(workspace_dir)


def _provision_k8s_namespace(request: ResourceRequest) -> dict:
    config = request.config or {}
    workspace_dir = _create_workspace(request.id, "k8s_namespace")

    _write_provider_config(workspace_dir, "kubernetes")

    quota = config.get("quota", "standard")

    quota_mapping = {
        "small": {"cpu": "1", "memory": "2Gi", "pods": "10"},
        "standard": {"cpu": "2", "memory": "4Gi", "pods": "20"},
        "large": {"cpu": "4", "memory": "8Gi", "pods": "50"}
    }

    quota_config = quota_mapping.get(quota, quota_mapping["standard"])

    main_tf = f'''
module "k8s_namespace" {{
  source = "{TERRAFORM_MODULES_PATH}/k8s_namespace"

  name                  = var.name
  quota_enabled         = var.quota_enabled
  quota_cpu_requests    = var.quota_cpu_requests
  quota_memory_requests = var.quota_memory_requests
  quota_pods            = var.quota_pods
  request_id            = var.request_id
  team_id               = var.team_id
}}

output "namespace_name" {{
  value = module.k8s_namespace.namespace_name
}}
'''

    tfvars = f'''
name                  = "{request.name}"
quota_enabled         = true
quota_cpu_requests    = "{quota_config['cpu']}"
quota_memory_requests = "{quota_config['memory']}"
quota_pods            = "{quota_config['pods']}"
request_id            = "{request.id}"
team_id               = "{request.team_id}"
kubeconfig_path       = "{config.get('kubeconfig', '~/.kube/config')}"
'''

    with open(os.path.join(workspace_dir, "main.tf"), "w") as f:
        f.write(main_tf)

    with open(os.path.join(workspace_dir, "terraform.tfvars"), "w") as f:
        f.write(tfvars)

    return _run_terraform_workflow(workspace_dir)


def _run_terraform_workflow(workspace_dir: str) -> dict:
    logger.info(f"Running Terraform in {workspace_dir} (DRY_RUN={DRY_RUN_MODE})")

    init_result = _run_terraform(workspace_dir, ["init", "-no-color"])
    if not init_result["success"]:
        return {"success": False, "error": f"Terraform init failed:\n{init_result['error']}"}

    plan_result = _run_terraform(workspace_dir, ["plan", "-no-color", "-out=tfplan"])
    if not plan_result["success"]:
        return {"success": False, "error": f"Terraform plan failed:\n{plan_result['error']}"}

    if DRY_RUN_MODE:
        logger.info("DRY RUN MODE: Skipping terraform apply")
        return {
            "success": True,
            "output": f"[DRY RUN] Plan completed successfully.\nWorkspace: {workspace_dir}\n\nPlan output:\n{plan_result['output'][:2000]}"
        }

    apply_result = _run_terraform(workspace_dir, ["apply", "-no-color", "-auto-approve", "tfplan"])
    if not apply_result["success"]:
        return {"success": False, "error": f"Terraform apply failed:\n{apply_result['error']}"}

    output_result = _run_terraform(workspace_dir, ["output", "-json"])
    if output_result["success"]:
        try:
            outputs = json.loads(output_result["output"])
            output_str = "\n".join([f"{k}: {v.get('value', 'N/A')}" for k, v in outputs.items()])
            return {"success": True, "output": output_str}
        except:
            return {"success": True, "output": apply_result["output"]}

    return {"success": True, "output": apply_result["output"]}


def _run_terraform(workspace_dir: str, command: list) -> dict:
    try:
        logger.info(f"Running: terraform {' '.join(command)}")

        result = subprocess.run(
            ["terraform"] + command,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0:
            logger.info(f"Terraform command succeeded")
            return {"success": True, "output": result.stdout}
        else:
            logger.error(f"Terraform command failed: {result.stderr}")
            return {"success": False, "error": result.stderr or result.stdout}

    except subprocess.TimeoutExpired:
        logger.error("Terraform command timed out")
        return {"success": False, "error": "Terraform command timed out after 10 minutes"}
    except FileNotFoundError:
        logger.error("Terraform not found")
        return {"success": False, "error": "Terraform CLI not found. Please install Terraform."}
    except Exception as e:
        logger.error(f"Terraform error: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def destroy_resource(self, request_id: int):
    db = SessionLocal()

    try:
        request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()

        if not request:
            return {"status": "error", "message": "Request not found"}

        workspace_dir = os.path.join(TERRAFORM_WORKSPACES_PATH, f"request-{request_id}")

        if not os.path.exists(workspace_dir):
            return {"status": "error", "message": "Workspace not found"}

        logger.info(f"Destroying resources for request {request_id}")

        destroy_result = _run_terraform(workspace_dir, ["destroy", "-no-color", "-auto-approve"])

        if destroy_result["success"]:
            request.status = "destroyed"
            request.admin_notes = f"{request.admin_notes or ''}\n\nResources destroyed successfully"
            shutil.rmtree(workspace_dir, ignore_errors=True)
        else:
            request.admin_notes = f"{request.admin_notes or ''}\n\nDestroy failed:\n{destroy_result['error']}"

        db.commit()
        return {"status": request.status, "request_id": request_id}

    except Exception as e:
        logger.error(f"Error destroying request {request_id}: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
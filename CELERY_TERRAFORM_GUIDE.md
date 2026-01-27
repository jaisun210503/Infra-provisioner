# Celery + Terraform Integration Guide

This guide explains every part of the Celery setup and Terraform integration line by line.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Celery Setup](#celery-setup)
3. [Terraform Modules](#terraform-modules)
4. [Terraform Tasks Code](#terraform-tasks-code)
5. [How Everything Connects](#how-everything-connects)

---

## Architecture Overview

```
┌────────────────┐     ┌─────────────┐     ┌────────────────┐
│    FastAPI     │────▶│    Redis    │────▶│ Celery Worker  │
│  (API Server)  │     │  (Broker)   │     │ (Task Runner)  │
└────────────────┘     └─────────────┘     └────────────────┘
        │                                          │
        │ 1. Admin approves request                │ 3. Worker runs Terraform
        ▼                                          ▼
┌────────────────┐                        ┌────────────────┐
│   SQLite DB    │◀───────────────────────│   Terraform    │
│                │  4. Update status       │   Workspace    │
└────────────────┘                        └────────────────┘
```

**Flow:**
1. Admin approves a resource request via API
2. FastAPI sends task to Redis queue
3. Celery worker picks up task and runs Terraform
4. Worker updates database with result

---

## Celery Setup

### File: `celery_app/__init__.py`

```python
from celery import Celery
```
**Line 1:** Import the `Celery` class from the celery library. This is the main class for creating Celery applications.

```python
celery_app = Celery(
    "infrautomater",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```
**Lines 3-7:** Create a Celery application instance.
- `"infrautomater"` - Name of the Celery app (used in logs)
- `broker="redis://..."` - Message broker URL. Redis stores the task queue.
  - `localhost:6379` - Redis server address and port
  - `/0` - Redis database number (Redis has 16 databases, 0-15)
- `backend="redis://..."` - Result backend. Where task results are stored.

```python
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
)
```
**Lines 9-17:** Configure Celery settings.
- `task_serializer="json"` - How to serialize task arguments (JSON format)
- `result_serializer="json"` - How to serialize task results
- `accept_content=["json"]` - Only accept JSON content (security)
- `timezone="UTC"` - Use UTC timezone for scheduling
- `enable_utc=True` - Store times in UTC
- `task_track_started=True` - Track when tasks start (not just finish)
- `task_time_limit=600` - Max 10 minutes per task (prevents hung tasks)

```python
celery_app.autodiscover_tasks(["celery_app.tasks"])
```
**Line 19:** Automatically find and register tasks from `celery_app.tasks` package.
- Celery looks for functions decorated with `@celery_app.task`
- This means you don't have to manually import each task

---

### File: `celery_app/celery_config.py`

```python
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
```
**Lines 1-2:** Alternative way to configure broker (we use inline config instead).

```python
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
```
**Lines 4-6:** Serialization settings.

```python
timezone = "UTC"
enable_utc = True
```
**Lines 8-9:** Timezone settings.

```python
task_track_started = True
task_time_limit = 600
```
**Lines 11-12:** Task tracking and timeout.

```python
task_acks_late = True
task_reject_on_worker_lost = True
```
**Lines 14-15:** Reliability settings.
- `task_acks_late=True` - Acknowledge task AFTER completion (not before)
  - If worker crashes mid-task, task goes back to queue
- `task_reject_on_worker_lost=True` - Reject task if worker dies

---

## Terraform Modules

### Directory Structure
```
terraform/
├── modules/           # Reusable Terraform modules
│   ├── database/      # AWS RDS module
│   ├── s3/            # AWS S3 module
│   └── k8s_namespace/ # Kubernetes namespace module
└── workspaces/        # Per-request workspaces (generated)
    └── request-{id}/  # Each request gets its own folder
```

### Database Module: `terraform/modules/database/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```
**Lines 1-8:** Terraform configuration block.
- `required_providers` - Declares which providers this module needs
- `aws` - The AWS provider from HashiCorp
- `source = "hashicorp/aws"` - Provider location (Terraform Registry)
- `version = "~> 5.0"` - Use version 5.x (any minor version of 5)

```hcl
resource "aws_db_instance" "database" {
  identifier     = var.name
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class
```
**Lines 10-15:** Create an RDS database instance.
- `resource` - Terraform keyword to create infrastructure
- `"aws_db_instance"` - Resource type (AWS RDS)
- `"database"` - Local name (used to reference this resource)
- `identifier = var.name` - DB identifier from variable
- `engine` - Database engine (postgres, mysql, etc.)
- `instance_class` - Server size (db.t3.micro, db.t3.small, etc.)

```hcl
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
```
**Lines 17-19:** Storage configuration.
- `allocated_storage` - Initial disk size in GB
- `max_allocated_storage` - Max size for autoscaling
- `storage_type = "gp3"` - SSD storage type (General Purpose 3)

```hcl
  db_name  = var.db_name
  username = var.username
  password = var.password
```
**Lines 21-23:** Database credentials.
- `db_name` - Name of the database to create
- `username` - Master username
- `password` - Master password (should be sensitive)

```hcl
  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = var.subnet_group_name
  publicly_accessible    = var.publicly_accessible
```
**Lines 25-27:** Network configuration.
- `vpc_security_group_ids` - Firewall rules
- `db_subnet_group_name` - Which subnets to use
- `publicly_accessible` - Allow internet access (usually false)

```hcl
  skip_final_snapshot    = true
  deletion_protection    = false
```
**Lines 29-30:** Deletion settings (for dev/test).
- `skip_final_snapshot` - Don't create backup when deleting
- `deletion_protection` - Allow deletion without extra steps

```hcl
  tags = merge(var.tags, {
    Name        = var.name
    ManagedBy   = "infrautomater"
    RequestId   = var.request_id
    TeamId      = var.team_id
  })
```
**Lines 32-37:** Resource tags.
- `merge()` - Combine multiple maps
- `ManagedBy = "infrautomater"` - Identify our resources
- `RequestId` - Link back to our application

---

### Database Module: `terraform/modules/database/variables.tf`

```hcl
variable "name" {
  type        = string
  description = "Database instance identifier"
}
```
**Lines 1-4:** Variable declaration.
- `variable "name"` - Declare a variable named "name"
- `type = string` - Must be a string value
- `description` - Human-readable explanation

```hcl
variable "engine" {
  type        = string
  default     = "postgres"
  description = "Database engine (postgres, mysql, mariadb)"
}
```
**Lines 6-10:** Variable with default value.
- `default = "postgres"` - If not provided, use postgres
- User can override by passing different value

```hcl
variable "password" {
  type        = string
  sensitive   = true
  description = "Master password"
}
```
**Lines 46-50:** Sensitive variable.
- `sensitive = true` - Don't show in logs/output

---

### Database Module: `terraform/modules/database/outputs.tf`

```hcl
output "endpoint" {
  value       = aws_db_instance.database.endpoint
  description = "Database endpoint"
}
```
**Lines 1-4:** Output declaration.
- `output "endpoint"` - Declare an output named "endpoint"
- `value = aws_db_instance.database.endpoint` - Get endpoint from resource
  - `aws_db_instance.database` - Reference to resource we created
  - `.endpoint` - Attribute of that resource
- This value is shown after `terraform apply`

---

### S3 Module: `terraform/modules/s3/main.tf`

```hcl
resource "aws_s3_bucket" "bucket" {
  bucket = var.name

  tags = merge(var.tags, {
    Name      = var.name
    ManagedBy = "infrautomater"
  })
}
```
**Lines 10-18:** Create S3 bucket.
- `bucket = var.name` - Bucket name (must be globally unique)

```hcl
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.bucket.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}
```
**Lines 20-27:** Enable/disable versioning.
- `bucket = aws_s3_bucket.bucket.id` - Reference to bucket we created
- `var.versioning_enabled ? "Enabled" : "Disabled"` - Ternary operator
  - If `versioning_enabled` is true, use "Enabled"
  - Otherwise, use "Disabled"

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```
**Lines 29-38:** Enable encryption.
- All objects automatically encrypted with AES-256

```hcl
resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket = aws_s3_bucket.bucket.id

  block_public_acls       = !var.public
  block_public_policy     = !var.public
  ignore_public_acls      = !var.public
  restrict_public_buckets = !var.public
}
```
**Lines 40-48:** Control public access.
- `!var.public` - Negate the public variable
- If `public = false`, all blocks are `true` (block everything)
- If `public = true`, all blocks are `false` (allow public)

---

### K8s Namespace Module: `terraform/modules/k8s_namespace/main.tf`

```hcl
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}
```
**Lines 1-8:** Require Kubernetes provider.

```hcl
resource "kubernetes_namespace" "namespace" {
  metadata {
    name = var.name

    labels = merge(var.labels, {
      "managed-by" = "infrautomater"
      "request-id" = var.request_id
    })
  }
}
```
**Lines 10-20:** Create Kubernetes namespace.
- `metadata` - Namespace metadata (name, labels, annotations)
- `labels` - Key-value pairs for organizing resources

```hcl
resource "kubernetes_resource_quota" "quota" {
  count = var.quota_enabled ? 1 : 0
```
**Lines 22-23:** Conditional resource creation.
- `count = var.quota_enabled ? 1 : 0`
  - If `quota_enabled = true`, create 1 resource
  - If `quota_enabled = false`, create 0 resources (skip)
- This is Terraform's way of making resources optional

```hcl
  spec {
    hard = {
      "requests.cpu"    = var.quota_cpu_requests
      "requests.memory" = var.quota_memory_requests
      "limits.cpu"      = var.quota_cpu_limits
      "limits.memory"   = var.quota_memory_limits
      "pods"            = var.quota_pods
      "services"        = var.quota_services
    }
  }
```
**Lines 31-40:** Resource quota limits.
- `requests.cpu` - Total CPU requests allowed in namespace
- `requests.memory` - Total memory requests allowed
- `limits.cpu/memory` - Total limits allowed
- `pods` - Max number of pods
- `services` - Max number of services

---

## Terraform Tasks Code

### File: `celery_app/tasks/terraform_tasks.py`

#### Imports Section

```python
import os
import sys
import subprocess
import json
import logging
import shutil
import secrets
import string
```
**Lines 1-8:** Import required modules.
- `os` - Operating system functions (paths, directories)
- `sys` - System functions (modify Python path)
- `subprocess` - Run external commands (terraform)
- `json` - Parse JSON output from Terraform
- `logging` - Log messages
- `shutil` - File operations (remove directories)
- `secrets` - Generate secure random values
- `string` - String constants (letters, digits)

```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```
**Line 10:** Add project root to Python path.
- `__file__` - Current file path
- `os.path.abspath()` - Get absolute path
- `os.path.dirname()` - Get parent directory
- Called 3 times: file → tasks → celery_app → project root
- `sys.path.insert(0, ...)` - Add to beginning of import search path
- **Why?** Celery worker runs from different directory, needs to find our modules

```python
from celery_app import celery_app
from database import SessionLocal
from models import ResourceRequest
```
**Lines 12-14:** Import our modules.
- `celery_app` - The Celery instance
- `SessionLocal` - Database session factory
- `ResourceRequest` - SQLAlchemy model

```python
logger = logging.getLogger(__name__)
```
**Line 16:** Create logger for this module.
- `__name__` - Module name (celery_app.tasks.terraform_tasks)
- Used for logging: `logger.info("message")`

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERRAFORM_MODULES_PATH = os.path.join(BASE_DIR, "terraform", "modules")
TERRAFORM_WORKSPACES_PATH = os.path.join(BASE_DIR, "terraform", "workspaces")
```
**Lines 18-20:** Define paths.
- `BASE_DIR` - Project root directory
- `TERRAFORM_MODULES_PATH` - Where our modules are
- `TERRAFORM_WORKSPACES_PATH` - Where workspaces are created

```python
DRY_RUN_MODE = True
```
**Line 22:** Dry run flag.
- `True` - Only run `terraform plan` (no actual resources)
- `False` - Run full `terraform apply` (creates real resources)

---

#### Main Task Function

```python
@celery_app.task(bind=True, max_retries=3)
def provision_resource(self, request_id: int):
```
**Lines 25-26:** Define Celery task.
- `@celery_app.task` - Register this function as a Celery task
- `bind=True` - Pass task instance as first argument (`self`)
  - Allows calling `self.retry()` on failure
- `max_retries=3` - Retry up to 3 times on failure
- `request_id: int` - ID of the ResourceRequest to provision

```python
    db = SessionLocal()
```
**Line 27:** Create database session.
- `SessionLocal()` - Factory function from database.py
- Returns a new SQLAlchemy session

```python
    try:
        request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
```
**Lines 29-30:** Fetch the request from database.
- `db.query(ResourceRequest)` - Query ResourceRequest table
- `.filter(ResourceRequest.id == request_id)` - WHERE id = request_id
- `.first()` - Get first result (or None if not found)

```python
        if not request:
            logger.error(f"Request {request_id} not found")
            return {"status": "error", "message": "Request not found"}
```
**Lines 32-34:** Handle missing request.
- Return early if request doesn't exist

```python
        if request.status != "approved":
            logger.warning(f"Request {request_id} is not approved, skipping")
            return {"status": "skipped", "message": "Request not approved"}
```
**Lines 36-38:** Only provision approved requests.
- Safety check: don't provision pending/rejected requests

```python
        request.status = "provisioning"
        db.commit()
```
**Lines 42-43:** Update status to "provisioning".
- `db.commit()` - Save changes to database
- User can now see the request is being processed

```python
        result = _provision_by_type(request)
```
**Line 45:** Call appropriate provisioning function.
- `_provision_by_type` - Routes to correct handler based on resource_type
- Returns `{"success": True/False, "output"/"error": "..."}`

```python
        if result["success"]:
            request.status = "provisioned"
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioned successfully:\n{result.get('output', '')}"
        else:
            request.status = "failed"
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioning failed:\n{result.get('error', '')}"
```
**Lines 47-52:** Update status based on result.
- `request.admin_notes or ''` - Handle None case
- Append provisioning output to admin notes

```python
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
```
**Lines 59-71:** Error handling.
- Catch any exception
- Try to update status to "failed"
- `raise self.retry(exc=e, countdown=60)` - Retry task after 60 seconds
  - `exc=e` - Original exception
  - `countdown=60` - Wait 60 seconds before retry

```python
    finally:
        db.close()
```
**Lines 73-74:** Always close database session.
- `finally` - Runs whether success or failure
- Prevents connection leaks

---

#### Routing Function

```python
def _provision_by_type(request: ResourceRequest) -> dict:
    resource_type = request.resource_type
    config = request.config or {}
    name = request.name

    if resource_type == "database":
        return _provision_database(request)
    elif resource_type == "s3":
        return _provision_s3(request)
    elif resource_type == "k8s_namespace":
        return _provision_k8s_namespace(request)
    else:
        return {"success": False, "error": f"Unknown resource type: {resource_type}"}
```
**Lines 77-91:** Route to correct provisioner.
- `request.config or {}` - Default to empty dict if None
- Simple if/elif to call appropriate function
- Returns error for unknown types

---

#### Helper Functions

```python
def _generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```
**Lines 94-96:** Generate secure random password.
- `string.ascii_letters` - "abcd...XYZ"
- `string.digits` - "0123456789"
- `secrets.choice()` - Cryptographically secure random choice
- Generator expression creates `length` random characters

```python
def _create_workspace(request_id: int, resource_type: str) -> str:
    workspace_dir = os.path.join(TERRAFORM_WORKSPACES_PATH, f"request-{request_id}")
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir
```
**Lines 99-102:** Create workspace directory.
- Each request gets isolated directory: `terraform/workspaces/request-123/`
- `os.makedirs(..., exist_ok=True)` - Create dir, don't error if exists

```python
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
```
**Lines 105-125:** Generate provider configuration.
- Triple quotes for multi-line string
- This configures how Terraform connects to AWS

---

#### Database Provisioner

```python
def _provision_database(request: ResourceRequest) -> dict:
    config = request.config or {}
    workspace_dir = _create_workspace(request.id, "database")

    _write_provider_config(workspace_dir, "aws")
```
**Lines 153-157:** Setup for database provisioning.
- Get config from request
- Create workspace directory
- Write AWS provider config

```python
    engine = config.get("engine", "postgres")
    size = config.get("size", "small")

    size_mapping = {
        "small": "db.t3.micro",
        "medium": "db.t3.small",
        "large": "db.t3.medium",
        "xlarge": "db.t3.large"
    }
```
**Lines 159-167:** Map user-friendly sizes to AWS instance types.
- User requests "small"
- We translate to "db.t3.micro"

```python
    main_tf = f'''
module "database" {{
  source = "{TERRAFORM_MODULES_PATH}/database"

  name             = var.name
  engine           = var.engine
  ...
}}
'''
```
**Lines 175-200:** Generate main.tf dynamically.
- `f'''...'''` - f-string with triple quotes
- `{{` and `}}` - Escaped braces (literal `{` in output)
- `{TERRAFORM_MODULES_PATH}` - Python variable (substituted)
- This creates Terraform code that uses our module

```python
    tfvars = f'''
name           = "{request.name}"
engine         = "{engine}"
...
'''
```
**Lines 203-214:** Generate terraform.tfvars.
- Contains actual values for variables
- `name = "my-database"` etc.

```python
    with open(os.path.join(workspace_dir, "main.tf"), "w") as f:
        f.write(main_tf)

    with open(os.path.join(workspace_dir, "terraform.tfvars"), "w") as f:
        f.write(tfvars)
```
**Lines 216-220:** Write files to workspace.
- `with open(..., "w")` - Open for writing, auto-close
- `f.write()` - Write content

```python
    return _run_terraform_workflow(workspace_dir)
```
**Line 222:** Run Terraform and return result.

---

#### Terraform Execution

```python
def _run_terraform_workflow(workspace_dir: str) -> dict:
    logger.info(f"Running Terraform in {workspace_dir} (DRY_RUN={DRY_RUN_MODE})")

    init_result = _run_terraform(workspace_dir, ["init", "-no-color"])
    if not init_result["success"]:
        return {"success": False, "error": f"Terraform init failed:\n{init_result['error']}"}
```
**Lines 329-334:** Initialize Terraform.
- `terraform init` - Download providers, setup workspace
- `-no-color` - Plain text output (no ANSI colors)

```python
    plan_result = _run_terraform(workspace_dir, ["plan", "-no-color", "-out=tfplan"])
    if not plan_result["success"]:
        return {"success": False, "error": f"Terraform plan failed:\n{plan_result['error']}"}
```
**Lines 336-338:** Create execution plan.
- `terraform plan` - Show what will be created/changed
- `-out=tfplan` - Save plan to file (for apply)

```python
    if DRY_RUN_MODE:
        logger.info("DRY RUN MODE: Skipping terraform apply")
        return {
            "success": True,
            "output": f"[DRY RUN] Plan completed successfully.\nWorkspace: {workspace_dir}\n\nPlan output:\n{plan_result['output'][:2000]}"
        }
```
**Lines 340-345:** Dry run mode.
- Skip apply if `DRY_RUN_MODE = True`
- Return plan output instead

```python
    apply_result = _run_terraform(workspace_dir, ["apply", "-no-color", "-auto-approve", "tfplan"])
    if not apply_result["success"]:
        return {"success": False, "error": f"Terraform apply failed:\n{apply_result['error']}"}
```
**Lines 347-349:** Apply the plan.
- `terraform apply` - Create actual resources
- `-auto-approve` - Don't prompt for confirmation
- `"tfplan"` - Use saved plan file

```python
    output_result = _run_terraform(workspace_dir, ["output", "-json"])
    if output_result["success"]:
        try:
            outputs = json.loads(output_result["output"])
            output_str = "\n".join([f"{k}: {v.get('value', 'N/A')}" for k, v in outputs.items()])
            return {"success": True, "output": output_str}
```
**Lines 351-356:** Get outputs.
- `terraform output -json` - Get outputs in JSON format
- Parse JSON and format as readable string
- Return endpoint, ARN, etc.

---

#### Run Terraform Command

```python
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
```
**Lines 362-372:** Execute Terraform command.
- `subprocess.run()` - Run external command
- `["terraform"] + command` - Build command list: ["terraform", "init", "-no-color"]
- `cwd=workspace_dir` - Run in workspace directory
- `capture_output=True` - Capture stdout and stderr
- `text=True` - Return strings (not bytes)
- `timeout=600` - 10 minute timeout

```python
        if result.returncode == 0:
            logger.info(f"Terraform command succeeded")
            return {"success": True, "output": result.stdout}
        else:
            logger.error(f"Terraform command failed: {result.stderr}")
            return {"success": False, "error": result.stderr or result.stdout}
```
**Lines 374-379:** Check result.
- `returncode == 0` - Success
- `returncode != 0` - Failure
- Return appropriate result dict

```python
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Terraform command timed out after 10 minutes"}
    except FileNotFoundError:
        return {"success": False, "error": "Terraform CLI not found. Please install Terraform."}
```
**Lines 381-384:** Handle exceptions.
- `TimeoutExpired` - Command took too long
- `FileNotFoundError` - Terraform not installed

---

#### Destroy Task

```python
@celery_app.task(bind=True)
def destroy_resource(self, request_id: int):
```
**Lines 392-393:** Task to destroy provisioned resources.

```python
    workspace_dir = os.path.join(TERRAFORM_WORKSPACES_PATH, f"request-{request_id}")

    if not os.path.exists(workspace_dir):
        return {"status": "error", "message": "Workspace not found"}
```
**Lines 401-404:** Find workspace.
- Can only destroy if workspace exists
- Workspace contains Terraform state

```python
    destroy_result = _run_terraform(workspace_dir, ["destroy", "-no-color", "-auto-approve"])

    if destroy_result["success"]:
        request.status = "destroyed"
        shutil.rmtree(workspace_dir, ignore_errors=True)
```
**Lines 408-413:** Destroy resources.
- `terraform destroy` - Delete all resources
- `shutil.rmtree()` - Remove workspace directory

---

## How Everything Connects

### Request Flow

1. **User submits request**
   ```
   POST /api/v1/users/requests/submit
   Body: {"name": "my-db", "resource_type": "database", "config": {"engine": "postgres"}}
   ```

2. **Admin approves**
   ```
   PUT /api/v1/admin/requests/1/approve
   ```

3. **FastAPI triggers Celery task**
   ```python
   # In admin_routes/requests.py
   provision_resource.delay(request.id)
   ```

4. **Task goes to Redis queue**
   ```
   Redis: LPUSH celery {"task": "provision_resource", "args": [1]}
   ```

5. **Celery worker picks up task**
   ```
   Worker: Received task provision_resource[uuid]
   ```

6. **Worker creates Terraform workspace**
   ```
   terraform/workspaces/request-1/
   ├── provider.tf    # AWS provider config
   ├── main.tf        # Module usage
   └── terraform.tfvars  # Variable values
   ```

7. **Worker runs Terraform**
   ```bash
   cd terraform/workspaces/request-1
   terraform init
   terraform plan -out=tfplan
   terraform apply -auto-approve tfplan
   terraform output -json
   ```

8. **Worker updates database**
   ```
   UPDATE resource_requests SET status='provisioned' WHERE id=1
   ```

### Workspace Contents After Provisioning

```
terraform/workspaces/request-1/
├── provider.tf           # Provider configuration
├── main.tf               # Module usage
├── terraform.tfvars      # Variable values
├── tfplan                 # Saved plan
├── .terraform/           # Downloaded providers
│   └── providers/
│       └── hashicorp/
│           └── aws/
└── terraform.tfstate     # Current state (IMPORTANT!)
```

The `terraform.tfstate` file tracks what was created. Without it, Terraform can't manage or destroy resources.

---

## Key Concepts Summary

| Concept | Explanation |
|---------|-------------|
| **Celery Task** | Background job that runs independently of web request |
| **Redis Broker** | Message queue that holds tasks waiting to be processed |
| **Terraform Module** | Reusable infrastructure template |
| **Terraform Workspace** | Isolated directory with its own state |
| **Provider** | Plugin that talks to cloud API (AWS, K8s, etc.) |
| **Resource** | Infrastructure component (database, bucket, etc.) |
| **Variable** | Input parameter for Terraform |
| **Output** | Value exported after apply (endpoint, ARN, etc.) |
| **State** | Record of what Terraform has created |
| **Plan** | Preview of changes before apply |
| **Apply** | Actually create/modify resources |
| **Destroy** | Delete all resources in state |

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Terraform not found" | CLI not installed | `brew install terraform` |
| "Connection refused" (Redis) | Redis not running | `brew services start redis` |
| "No module named 'database'" | Import path issue | Check sys.path setup |
| "Access Denied" (AWS) | No credentials | Run `aws configure` |
| "Bucket already exists" | S3 names are global | Use unique bucket names |
| Task stays "pending" | Worker not running | Start Celery worker |

---

*Last updated: Session 2026-01-26*
import os
import sys
import subprocess
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from celery_app import celery_app
from database import SessionLocal
from models import ResourceRequest

logger = logging.getLogger(__name__)

TERRAFORM_BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "terraform")


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
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioned successfully: {result.get('output', '')}"
        else:
            request.status = "failed"
            request.admin_notes = f"{request.admin_notes or ''}\n\nProvisioning failed: {result.get('error', '')}"

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
        return _provision_database(name, config)
    elif resource_type == "s3":
        return _provision_s3(name, config)
    elif resource_type == "k8s_namespace":
        return _provision_k8s_namespace(name, config)
    else:
        return {"success": False, "error": f"Unknown resource type: {resource_type}"}


def _provision_database(name: str, config: dict) -> dict:
    logger.info(f"[SIMULATED] Creating database: {name}")
    logger.info(f"  Engine: {config.get('engine', 'postgres')}")
    logger.info(f"  Size: {config.get('size', 'small')}")

    return {
        "success": True,
        "output": f"Database {name} created with engine={config.get('engine', 'postgres')}"
    }


def _provision_s3(name: str, config: dict) -> dict:
    logger.info(f"[SIMULATED] Creating S3 bucket: {name}")
    logger.info(f"  Region: {config.get('region', 'us-east-1')}")
    logger.info(f"  Public: {config.get('public', False)}")

    return {
        "success": True,
        "output": f"S3 bucket {name} created in {config.get('region', 'us-east-1')}"
    }


def _provision_k8s_namespace(name: str, config: dict) -> dict:
    logger.info(f"[SIMULATED] Creating K8s namespace: {name}")
    logger.info(f"  Cluster: {config.get('cluster', 'default')}")
    logger.info(f"  Quota: {config.get('quota', 'standard')}")

    return {
        "success": True,
        "output": f"K8s namespace {name} created in cluster {config.get('cluster', 'default')}"
    }


def _run_terraform(working_dir: str, command: list) -> dict:
    try:
        result = subprocess.run(
            ["terraform"] + command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Terraform command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
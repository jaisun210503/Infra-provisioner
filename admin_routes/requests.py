from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, ResourceRequest
from schemas import (
    ResourceRequestResponse,
    ResourceRequestApproval,
    ResourceRequestRejection
)
from auth.auth import get_current_admin_user
from celery_app.tasks.terraform_tasks import provision_resource

admin_request_router = APIRouter(prefix="/api/v1/admin", tags=["Admin Requests"])


# 1. GET /requests - View all resource requests (with optional filtering)
@admin_request_router.get("/requests", response_model=List[ResourceRequestResponse])
def view_all_requests(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(ResourceRequest)

    # Filter by status if provided
    if status_filter:
        query = query.filter(ResourceRequest.status == status_filter)

    # Order by newest first
    requests = query.order_by(ResourceRequest.created_at.desc()).all()
    return requests


# 2. GET /requests/{id} - Get specific request details
@admin_request_router.get("/requests/{request_id}", response_model=ResourceRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


# 3. PUT /requests/{id}/approve - Approve request
@admin_request_router.put("/requests/{request_id}/approve", response_model=ResourceRequestResponse)
def approve_request(
    request_id: int,
    approval: ResourceRequestApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Find the request
    request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()

    # Check if exists
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Check if already processed
    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Request already {request.status}"
        )

    # Update status and notes
    request.status = "approved"
    request.admin_notes = approval.admin_notes

    # Save to database
    db.commit()
    db.refresh(request)

    # Trigger Celery task for Terraform provisioning
    provision_resource.delay(request.id)

    return request


# 4. PUT /requests/{id}/reject - Reject request
@admin_request_router.put("/requests/{request_id}/reject", response_model=ResourceRequestResponse)
def reject_request(
    request_id: int,
    rejection: ResourceRequestRejection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Find the request
    request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()

    # Check if exists
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Check if already processed
    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Request already {request.status}"
        )

    # Update status and notes (notes required for rejection)
    request.status = "rejected"
    request.admin_notes = rejection.admin_notes

    # Save to database
    db.commit()
    db.refresh(request)

    return request
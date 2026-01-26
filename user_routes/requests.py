from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, ResourceRequest
from schemas import (
    ResourceRequestCreate,
    ResourceRequestResponse,
    ResourceRequestUpdate
)
from auth.auth import get_current_user

request_router = APIRouter(prefix="/api/v1/users", tags=["User Requests"])


# TODO: Add your endpoints here
# 1. POST /requests - Submit new resource request
# 2. GET /requests - View my requests
# 3. GET /requests/{id} - Get specific request details

    

@request_router.post("/requests/submit",response_model=ResourceRequestResponse)
def submit_request(request:ResourceRequestCreate,db: Session = Depends(get_db),user = Depends(get_current_user)):
    if request.resource_type and request.name is not None:
        resource_request = ResourceRequest(
            name = request.name,
            resource_type = request.resource_type,
            config = request.config,
            user_id=user.id,           # ← Add this                                                                                                      
            team_id=user.team_id
              )
        db.add(resource_request)
        db.commit()
        db.refresh(resource_request)
    return resource_request


@request_router.get("/requests",response_model=List[ResourceRequestResponse])
def view_my_requests(db: Session = Depends(get_db), user = Depends(get_current_user)):
    requests = db.query(ResourceRequest).filter(ResourceRequest.user_id == user.id).all()
    return requests


@request_router.get("/requests/{request_id}",response_model=ResourceRequestResponse)
def get_my_request(request_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    request = db.query(ResourceRequest).filter(
        ResourceRequest.id == request_id,
        ResourceRequest.user_id == user.id
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

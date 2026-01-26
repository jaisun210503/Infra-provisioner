from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ============ Token Schemas ============
class Token(BaseModel):
    access_token: str
    token_type: str


# ============ User Schemas ============
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    username: str
    email: str


class UserResponse(UserBase):
    id: int
    is_admin: bool
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Team Schemas ============
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(TeamBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamWithMembers(TeamResponse):
    members: List[UserResponse] = []


# ============ Member Schemas ============
class AddMemberRequest(BaseModel):
    user_id: int

class TeamDetails(BaseModel):
    id: str


# ============ Resource Request Schemas ============
class ResourceRequestBase(BaseModel):
    resource_type: str  # "database", "s3", "k8s_namespace"
    name: str
    config: Optional[dict] = None


class ResourceRequestCreate(ResourceRequestBase):
    pass


class ResourceRequestUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None


class ResourceRequestResponse(ResourceRequestBase):
    id: int
    user_id: int
    team_id: Optional[int] = None
    status: str  # "pending", "approved", "rejected"
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceRequestApproval(BaseModel):
    admin_notes: Optional[str] = None


class ResourceRequestRejection(BaseModel):
    admin_notes: str  # Required when rejecting
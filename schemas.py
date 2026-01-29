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
        orm_mode = True


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
        orm_mode = True


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
        orm_mode = True


class ResourceRequestApproval(BaseModel):
    admin_notes: Optional[str] = None


class ResourceRequestRejection(BaseModel):
    admin_notes: str  # Required when rejecting


# ============ AWS Credentials Schemas ============
class AWSCredentialsCreate(BaseModel):
    team_id: Optional[int] = None
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    aws_session_token: Optional[str] = None


class AWSCredentialsResponse(BaseModel):
    id: int
    team_id: Optional[int]
    aws_region: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AWSCredentialsTestResult(BaseModel):
    success: bool
    message: str
    account_id: Optional[str] = None
    user_arn: Optional[str] = None
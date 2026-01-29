"""
Admin routes for managing AWS credentials.
Allows admins to configure per-team or global AWS credentials.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth.auth import get_current_user
from database import get_db
from models import User, AWSCredentials, Team
from schemas import (
    AWSCredentialsCreate,
    AWSCredentialsResponse,
    AWSCredentialsTestResult
)
from utils.encryption import encrypt_credential, decrypt_credential

aws_credentials_router = APIRouter(
    prefix="/api/v1/admin/aws-credentials",
    tags=["Admin - AWS Credentials"]
)


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@aws_credentials_router.get("", response_model=List[AWSCredentialsResponse])
def list_aws_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all configured AWS credentials (no secrets exposed).
    """
    credentials = db.query(AWSCredentials).filter(
        AWSCredentials.is_active == True
    ).all()
    return credentials


@aws_credentials_router.get("/{team_id}", response_model=AWSCredentialsResponse)
def get_team_credentials(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get AWS credentials for a specific team.
    """
    credentials = db.query(AWSCredentials).filter(
        AWSCredentials.team_id == team_id,
        AWSCredentials.is_active == True
    ).first()

    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found for this team")

    return credentials


@aws_credentials_router.post("", response_model=AWSCredentialsResponse)
def create_or_update_credentials(
    credentials_data: AWSCredentialsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create or update AWS credentials for a team or globally.
    If team_id is provided, creates team-specific credentials.
    If team_id is None, creates global default credentials.
    """
    # Validate team exists if team_id provided
    if credentials_data.team_id:
        team = db.query(Team).filter(Team.id == credentials_data.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

    # Check if credentials already exist
    existing = db.query(AWSCredentials).filter(
        AWSCredentials.team_id == credentials_data.team_id
    ).first()

    if existing:
        # Update existing credentials
        existing.aws_access_key_id_encrypted = encrypt_credential(
            credentials_data.aws_access_key_id
        )
        existing.aws_secret_access_key_encrypted = encrypt_credential(
            credentials_data.aws_secret_access_key
        )
        existing.aws_region = credentials_data.aws_region

        if credentials_data.aws_session_token:
            existing.aws_session_token_encrypted = encrypt_credential(
                credentials_data.aws_session_token
            )
        else:
            existing.aws_session_token_encrypted = None

        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    # Create new credentials
    new_credentials = AWSCredentials(
        team_id=credentials_data.team_id,
        aws_access_key_id_encrypted=encrypt_credential(
            credentials_data.aws_access_key_id
        ),
        aws_secret_access_key_encrypted=encrypt_credential(
            credentials_data.aws_secret_access_key
        ),
        aws_session_token_encrypted=encrypt_credential(
            credentials_data.aws_session_token
        ) if credentials_data.aws_session_token else None,
        aws_region=credentials_data.aws_region,
        created_by=current_user.id,
        is_active=True
    )

    db.add(new_credentials)
    db.commit()
    db.refresh(new_credentials)

    return new_credentials


@aws_credentials_router.post("/test", response_model=AWSCredentialsTestResult)
def test_aws_credentials(
    credentials_data: AWSCredentialsCreate,
    current_user: User = Depends(require_admin)
):
    """
    Test AWS credentials by making a simple AWS STS call.
    Does not save credentials to database.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

        # Create STS client with provided credentials
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=credentials_data.aws_access_key_id,
            aws_secret_access_key=credentials_data.aws_secret_access_key,
            aws_session_token=credentials_data.aws_session_token,
            region_name=credentials_data.aws_region
        )

        # Test credentials by getting caller identity
        response = sts_client.get_caller_identity()

        return AWSCredentialsTestResult(
            success=True,
            message="Credentials are valid",
            account_id=response.get('Account'),
            user_arn=response.get('Arn')
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']

        return AWSCredentialsTestResult(
            success=False,
            message=f"AWS Error ({error_code}): {error_message}"
        )

    except Exception as e:
        return AWSCredentialsTestResult(
            success=False,
            message=f"Connection error: {str(e)}"
        )


@aws_credentials_router.delete("/{team_id}")
def delete_credentials(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete AWS credentials for a team (soft delete by setting is_active=False).
    """
    credentials = db.query(AWSCredentials).filter(
        AWSCredentials.team_id == team_id
    ).first()

    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found for this team")

    # Soft delete
    credentials.is_active = False
    db.commit()

    return {"message": "Credentials deleted successfully"}

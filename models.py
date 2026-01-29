from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey,  JSON
from sqlalchemy.orm import relationship
from database import Base


class Team(Base):
    """SQLAlchemy model for the teams table."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_teams", foreign_keys=[created_by])
    members = relationship("User", back_populates="team", foreign_keys="User.team_id")
    resource_requests = relationship("ResourceRequest", back_populates="team")


class User(Base):
    """SQLAlchemy model for the users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    created_teams = relationship("Team", back_populates="creator", foreign_keys="Team.created_by")
    resource_requests = relationship("ResourceRequest", back_populates="user")


class ResourceRequest(Base):
    __tablename__ = "resource_requests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    resource_type = Column(String(50), nullable=False)
    # "database", "s3", "k8s_namespace"

    name = Column(String(255), nullable=False)

    config = Column(JSON, nullable=True)
    # Use Text if your DB doesn't support JSON

    status = Column(String(20), default="pending", nullable=False)
    # "pending", "approved", "rejected"

    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resource_requests")
    team = relationship("Team", back_populates="resource_requests")


class AWSCredentials(Base):
    """SQLAlchemy model for AWS credentials with encryption."""

    __tablename__ = "aws_credentials"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, unique=True)

    # Encrypted fields
    aws_access_key_id_encrypted = Column(Text, nullable=False)
    aws_secret_access_key_encrypted = Column(Text, nullable=False)
    aws_session_token_encrypted = Column(Text, nullable=True)

    # Plaintext fields
    aws_region = Column(String(50), default="us-east-1")
    is_active = Column(Boolean, default=True)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    creator = relationship("User", foreign_keys=[created_by])
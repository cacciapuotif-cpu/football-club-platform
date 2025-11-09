"""User model with RBAC roles."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.organization import Organization


class UserRole(str, Enum):
    """User roles for RBAC."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    COACH = "COACH"
    ANALYST = "ANALYST"
    PHYSIO = "PHYSIO"
    DOCTOR = "DOCTOR"
    PLAYER = "PLAYER"
    PARENT = "PARENT"
    VIEWER = "VIEWER"
    MEDICAL = "MEDICAL"
    PSYCHOLOGIST = "PSYCHOLOGIST"


class User(SQLModel, table=True):
    """
    User model with authentication and RBAC.
    Multi-tenant: each user belongs to an organization (tenant).
    """

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.PLAYER)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    organization: "Organization" = Relationship(back_populates="users")

    # Player link (if role=PLAYER)
    player_id: UUID | None = Field(default=None, foreign_key="players.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    last_login_at: datetime | None = Field(default=None)

    # Security
    failed_login_attempts: int = Field(default=0)
    locked_until: datetime | None = Field(default=None)

    class Config:
        use_enum_values = True

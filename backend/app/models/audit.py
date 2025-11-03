"""Audit Log model for GDPR compliance."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel
from sqlalchemy import func, Index

if TYPE_CHECKING:
    pass


class AuditAction(str, Enum):
    """Audit log action types."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_DENIED = "ACCESS_DENIED"


class AuditLog(SQLModel, table=True):
    """
    Audit log for tracking access to sensitive data.
    GDPR requirement: 7 years retention.
    """

    __tablename__ = "audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True)
    )

    # Actor
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    user_email: str | None = Field(default=None, max_length=255)
    user_role: str | None = Field(default=None, max_length=50)

    # Action
    action: AuditAction
    resource_type: str = Field(max_length=100)  # player, injury, medical_data
    resource_id: UUID | None = None

    # Context
    ip_address: str | None = Field(default=None, max_length=50)
    user_agent: str | None = Field(default=None, max_length=500)
    endpoint: str | None = Field(default=None, max_length=500)

    # Details
    details: dict = Field(default={}, sa_column=Column(JSON))
    success: bool = Field(default=True)
    error_message: str | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    class Config:
        use_enum_values = True

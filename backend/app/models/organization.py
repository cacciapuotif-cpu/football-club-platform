"""Organization (Tenant) model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.team import Team


class Organization(SQLModel, table=True):
    """
    Organization (Club/Society) - Tenant for multi-tenancy.
    Each organization has its own isolated data.
    """

    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    slug: str = Field(unique=True, max_length=100, index=True)
    logo_url: str | None = Field(default=None, max_length=500)

    # Contact
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    country: str = Field(default="IT", max_length=2)

    # Settings
    is_active: bool = Field(default=True)
    benchmark_opt_in: bool = Field(default=False)  # Opt-in for anonymous benchmark
    timezone: str = Field(default="Europe/Rome", max_length=50)
    locale: str = Field(default="it-IT", max_length=10)

    # Quotas
    quota_players: int = Field(default=50)
    quota_storage_gb: int = Field(default=10)
    current_storage_gb: float = Field(default=0.0)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    users: list["User"] = Relationship(back_populates="organization")
    teams: list["Team"] = Relationship(back_populates="organization")

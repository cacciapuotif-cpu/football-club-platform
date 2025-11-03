"""Team and Season models."""

from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.player import Player


class Team(SQLModel, table=True):
    """Team/Squad within an organization."""

    __tablename__ = "teams"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    category: str | None = Field(default=None, max_length=100)  # U15, U17, U19, Serie C, etc.
    season_id: UUID | None = Field(default=None, foreign_key="seasons.id", index=True)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    organization: "Organization" = Relationship(back_populates="teams")

    # Relationships
    season: Optional["Season"] = Relationship(back_populates="teams")
    players: list["Player"] = Relationship(back_populates="team")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class Season(SQLModel, table=True):
    """Season (eg. 2024-2025)."""

    __tablename__ = "seasons"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)  # "2024-2025"
    start_date: date
    end_date: date
    is_active: bool = Field(default=True)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Relationships
    teams: list["Team"] = Relationship(back_populates="season")

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

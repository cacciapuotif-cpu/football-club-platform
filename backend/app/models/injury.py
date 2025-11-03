"""Injury tracking model."""

from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class InjuryType(str, Enum):
    """Types of injuries."""

    MUSCLE = "MUSCLE"
    LIGAMENT = "LIGAMENT"
    TENDON = "TENDON"
    BONE = "BONE"
    JOINT = "JOINT"
    CONCUSSION = "CONCUSSION"
    OTHER = "OTHER"


class InjurySeverity(str, Enum):
    """Injury severity levels."""

    MINOR = "MINOR"  # 1-7 days
    MODERATE = "MODERATE"  # 8-28 days
    SEVERE = "SEVERE"  # >28 days


class BodySide(str, Enum):
    """Body side."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BILATERAL = "BILATERAL"
    NA = "NA"


class Injury(SQLModel, table=True):
    """Injury tracking with medical data."""

    __tablename__ = "injuries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Injury details
    injury_date: date
    injury_type: InjuryType
    body_part: str = Field(max_length=100)  # Hamstring, Ankle, Knee, etc.
    body_side: BodySide = Field(default=BodySide.NA)
    severity: InjurySeverity

    # Context
    mechanism: str | None = Field(default=None, max_length=500)  # How it happened
    match_id: UUID | None = Field(default=None, foreign_key="matches.id")
    session_id: UUID | None = Field(default=None, foreign_key="training_sessions.id")

    # Recovery
    expected_return_date: date | None = None
    actual_return_date: date | None = None
    days_out: int | None = None
    is_recurrence: bool = Field(default=False)
    previous_injury_id: UUID | None = Field(default=None, foreign_key="injuries.id")

    # Medical
    diagnosis: str | None = Field(default=None, sa_column=Column(Text))
    treatment_plan: str | None = Field(default=None, sa_column=Column(Text))
    medical_clearance: bool = Field(default=False)
    clearance_date: date | None = None
    doctor_name: str | None = Field(default=None, max_length=255)

    # Status
    is_active: bool = Field(default=True)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True

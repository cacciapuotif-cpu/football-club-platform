"""Training Session model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class SessionType(str, Enum):
    """Training session types."""

    TRAINING = "TRAINING"
    TECHNICAL = "TECHNICAL"
    TACTICAL = "TACTICAL"
    PHYSICAL = "PHYSICAL"
    PSYCHOLOGICAL = "PSYCHOLOGICAL"
    FRIENDLY = "FRIENDLY"
    RECOVERY = "RECOVERY"
    GYM = "GYM"


class SessionIntensity(str, Enum):
    """Training session intensity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TrainingSession(SQLModel, table=True):
    """Training session model."""

    __tablename__ = "training_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_date: datetime
    session_type: SessionType = Field(default=SessionType.TRAINING)
    duration_min: int
    team_id: UUID = Field(foreign_key="teams.id", index=True)

    # Content
    focus: str | None = Field(default=None, max_length=255)  # Tecnico, Tattico, Fisico
    focus_area: str | None = Field(default=None, max_length=255)  # Specific area (passing, defense, etc.)
    description: str | None = Field(default=None, sa_column=Column(Text))
    coach_notes: str | None = Field(default=None, sa_column=Column(Text))

    # Intensity
    intensity: SessionIntensity | None = Field(default=SessionIntensity.MEDIUM)
    planned_intensity: int | None = Field(default=None)  # 1-10
    actual_intensity_avg: float | None = Field(default=None)  # From RPE

    # Video
    video_id: UUID | None = Field(default=None, foreign_key="videos.id", index=True)

    # GPS/Physical metrics from session
    distance_m: float | None = Field(default=None, ge=0)
    hi_distance_m: float | None = Field(default=None, ge=0)  # High intensity >20 km/h
    sprints_count: int | None = Field(default=None, ge=0)
    top_speed_ms: float | None = Field(default=None, ge=0, le=12)  # m/s
    max_acc_ms2: float | None = Field(default=None, ge=0, le=12)  # m/s²
    hr_avg_bpm: int | None = Field(default=None, ge=30, le=220)
    hr_max_bpm: int | None = Field(default=None, ge=30, le=220)
    fatigue_note: str | None = Field(default=None, max_length=500)

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

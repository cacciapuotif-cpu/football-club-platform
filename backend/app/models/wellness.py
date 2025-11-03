"""Wellness and recovery data models."""

from datetime import datetime, date
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel
from sqlalchemy import func


class WellnessData(SQLModel, table=True):
    """Daily wellness and recovery data."""

    __tablename__ = "wellness_data"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Sleep
    sleep_hours: float | None = None
    sleep_quality: int | None = None  # 1-5
    sleep_start_hhmm: str | None = Field(default=None, max_length=5)  # HH:MM
    wake_time_hhmm: str | None = Field(default=None, max_length=5)  # HH:MM

    # Body metrics
    body_weight_kg: float | None = Field(default=None, ge=0)

    # Recovery
    hrv_ms: float | None = None  # Heart Rate Variability
    resting_hr_bpm: int | None = None
    doms_rating: int | None = None  # Delayed Onset Muscle Soreness 1-5

    # Perceived state
    fatigue_rating: int | None = None  # 1-5
    stress_rating: int | None = None
    mood_rating: int | None = None
    motivation_rating: int | None = None

    # Hydration
    hydration_rating: int | None = None  # 1-5
    hydration_pct: float | None = Field(default=None, ge=0, le=100)  # % estimated

    # Session RPE (if training day)
    srpe: int | None = None  # Session RPE 1-10
    session_duration_min: int | None = None
    training_load: float | None = None  # sRPE * duration

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

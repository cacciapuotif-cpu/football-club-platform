"""
Training data with attendance tracking and EAV metrics structure.
Extends existing TrainingSession with per-player attendance and flexible metrics.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func, UniqueConstraint

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.session import TrainingSession


class TrainingAttendance(SQLModel, table=True):
    """
    Player attendance for a training session.
    Links player to session with participation details.
    """

    __tablename__ = "training_attendance"
    __table_args__ = (
        UniqueConstraint('training_session_id', 'player_id', name='uq_attendance_session_player'),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    training_session_id: UUID = Field(foreign_key="training_sessions.id", index=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Attendance
    status: str = Field(default="present", max_length=50)  # present, absent, injured, sick, late
    minutes: int | None = Field(default=None, ge=0, le=300)  # minutes participated
    participation_pct: int | None = Field(default=None, ge=0, le=100)  # % of session participated

    # Quick RPE (can also be stored as metric)
    rpe_post: int | None = Field(default=None, ge=1, le=10)  # Session RPE after training

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Relationships
    metrics: list["TrainingMetric"] = Relationship(back_populates="attendance")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class TrainingMetric(SQLModel, table=True):
    """
    Individual training metric for a player's attendance.
    EAV structure for flexible GPS/physical/RPE data.

    Standard metric_keys:
    - rpe_post (1-10)
    - hsr (m) - High Speed Running
    - sprint_count (#)
    - total_distance (km)
    - accel_count (#)
    - decel_count (#)
    - top_speed (km/h)
    - avg_hr (bpm)
    - max_hr (bpm)
    - player_load (AU)
    - metabolic_power (W/kg)
    """

    __tablename__ = "training_metrics"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    training_attendance_id: UUID = Field(foreign_key="training_attendance.id", index=True)

    # EAV structure
    metric_key: str = Field(index=True, max_length=100)
    metric_value: float
    unit: str | None = Field(default=None, max_length=50)  # 'm', 'km', 'bpm', '#', 'score', 'AU', 'W/kg'

    # Data quality
    validity: str = Field(default="valid", max_length=20)  # valid, invalid, suspect
    tags: str | None = Field(default=None, max_length=200)  # device_id, gps_quality, etc.

    # Relationships
    attendance: Optional["TrainingAttendance"] = Relationship(back_populates="metrics")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

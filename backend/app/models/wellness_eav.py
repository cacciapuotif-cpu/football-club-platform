"""
Wellness data with Entity-Attribute-Value (EAV) structure.
Replaces flat WellnessData model with flexible metric storage.
"""

from datetime import datetime
from datetime import date as DateType
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func, UniqueConstraint

if TYPE_CHECKING:
    from app.models.player import Player


class WellnessSession(SQLModel, table=True):
    """
    Daily wellness session for a player.
    Container for multiple wellness metrics.
    """

    __tablename__ = "wellness_sessions"
    __table_args__ = (
        UniqueConstraint('player_id', 'date', name='uq_wellness_session_player_date'),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: DateType = Field(index=True)

    # Metadata
    source: str | None = Field(default="manual", max_length=50)  # manual, app, import
    schema_version: int = Field(default=1)
    note: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Relationships
    metrics: list["WellnessMetric"] = Relationship(back_populates="session")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class WellnessMetric(SQLModel, table=True):
    """
    Individual wellness metric within a session.
    EAV structure allows flexible metrics without schema changes.

    Standard metric_keys:
    - sleep_quality (1-10)
    - sleep_hours (0-24)
    - stress (1-10)
    - fatigue (1-10)
    - doms (1-10) - Delayed Onset Muscle Soreness
    - mood (1-10)
    - motivation (1-10)
    - hydration (1-10)
    - rpe_morning (1-10)
    - body_weight_kg
    - resting_hr_bpm
    - hrv_ms
    """

    __tablename__ = "wellness_metrics"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    wellness_session_id: UUID = Field(foreign_key="wellness_sessions.id", index=True)

    # EAV structure
    metric_key: str = Field(index=True, max_length=100)  # e.g., 'sleep_quality', 'stress'
    metric_value: float
    unit: str | None = Field(default=None, max_length=50)  # 'score', 'hours', 'kg', 'bpm', 'ms'

    # Data quality
    validity: str = Field(default="valid", max_length=20)  # valid, invalid, suspect, interpolated
    tags: str | None = Field(default=None, max_length=200)  # JSON or comma-separated

    # Relationships
    session: Optional["WellnessSession"] = Relationship(back_populates="metrics")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

"""SQLModel definitions for core sessions & wellness domain."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint, func, JSON
from sqlmodel import Field, SQLModel


class AthleteStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Athlete(SQLModel, table=True):
    """Athlete entity mapped to athletes table."""

    __tablename__ = "athletes"

    athlete_id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    pii_token: Optional[str] = Field(default=None, max_length=255)
    status: AthleteStatus = Field(default=AthleteStatus.ACTIVE, sa_column=Column(String(50), nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class SessionType(str, Enum):
    TRAINING = "training"
    MATCH = "match"
    RECOVERY = "recovery"
    OTHER = "other"


class Session(SQLModel, table=True):
    """Session metadata (training, game, etc.)."""

    __tablename__ = "sessions"

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    team_id: UUID = Field(index=True, nullable=False)
    type: SessionType = Field(default=SessionType.TRAINING, sa_column=Column(String(50), nullable=False))
    start_ts: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_ts: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    rpe_avg: Optional[float] = Field(default=None)
    load: Optional[float] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text()))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class SessionParticipationStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    MISSED = "missed"
    EXCUSED = "excused"


class SessionParticipation(SQLModel, table=True):
    """Participation metrics per athlete per session."""

    __tablename__ = "session_participation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "session_id", "athlete_id", name="uix_session_participation_session_athlete"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    session_id: UUID = Field(index=True, nullable=False)
    athlete_id: UUID = Field(index=True, nullable=False)
    rpe: Optional[float] = Field(default=None)
    load: Optional[float] = Field(default=None)
    status: SessionParticipationStatus = Field(
        default=SessionParticipationStatus.COMPLETED,
        sa_column=Column(String(30), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class WellnessReading(SQLModel, table=True):
    """Raw wellness data points."""

    __tablename__ = "wellness_readings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    athlete_id: UUID = Field(index=True, nullable=False)
    source: str = Field(max_length=50)
    metric: str = Field(max_length=100)
    value: float
    unit: Optional[str] = Field(default=None, max_length=20)
    event_ts: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ingest_ts: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    quality_score: Optional[float] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class Feature(SQLModel, table=True):
    """Computed feature store values."""

    __tablename__ = "features"
    __table_args__ = (
        UniqueConstraint("tenant_id", "athlete_id", "feature_name", "event_ts", name="pk_features"),
    )

    tenant_id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(primary_key=True)
    feature_name: str = Field(primary_key=True, max_length=120)
    event_ts: datetime = Field(primary_key=True)
    feature_value: float
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class PredictionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Prediction(SQLModel, table=True):
    """Model outputs per athlete/day."""

    __tablename__ = "predictions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    athlete_id: UUID = Field(index=True, nullable=False)
    model_version: str = Field(max_length=50)
    score: float
    severity: PredictionSeverity = Field(
        default=PredictionSeverity.LOW,
        sa_column=Column(String(20), nullable=False),
    )
    drivers: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    event_ts: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    CLOSED = "closed"


class Alert(SQLModel, table=True):
    """Operational alerts tied to policies and sessions."""

    __tablename__ = "alerts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    athlete_id: UUID = Field(index=True, nullable=False)
    session_id: Optional[UUID] = Field(default=None, index=True)
    status: AlertStatus = Field(default=AlertStatus.OPEN, sa_column=Column(String(20), nullable=False))
    severity: PredictionSeverity = Field(default=PredictionSeverity.LOW, sa_column=Column(String(20), nullable=False))
    policy_id: Optional[str] = Field(default=None, max_length=50)
    opened_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    closed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ack_by: Optional[UUID] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
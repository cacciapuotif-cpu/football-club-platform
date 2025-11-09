"""Pydantic schemas for sessions & wellness resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.sessions_wellness import (
    AlertStatus,
    AthleteStatus,
    PredictionSeverity,
    SessionParticipationStatus,
    SessionType,
)


class AthleteBase(BaseModel):
    athlete_id: UUID
    tenant_id: UUID
    status: AthleteStatus
    pii_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    session_id: UUID
    tenant_id: UUID
    team_id: UUID
    type: SessionType
    start_ts: datetime
    end_ts: Optional[datetime]
    rpe_avg: Optional[float]
    load: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionParticipationBase(BaseModel):
    id: UUID
    tenant_id: UUID
    session_id: UUID
    athlete_id: UUID
    rpe: Optional[float]
    load: Optional[float]
    status: SessionParticipationStatus
    created_at: datetime

    class Config:
        from_attributes = True


class WellnessReadingBase(BaseModel):
    id: UUID
    tenant_id: UUID
    athlete_id: UUID
    source: str
    metric: str
    value: float
    unit: Optional[str]
    event_ts: datetime
    ingest_ts: datetime
    quality_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class FeatureBase(BaseModel):
    tenant_id: UUID
    athlete_id: UUID
    feature_name: str
    feature_value: float
    event_ts: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionBase(BaseModel):
    id: UUID
    tenant_id: UUID
    athlete_id: UUID
    model_version: str
    score: float = Field(ge=0.0)
    severity: PredictionSeverity
    drivers: Optional[dict]
    event_ts: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    id: UUID
    tenant_id: UUID
    athlete_id: UUID
    session_id: Optional[UUID]
    status: AlertStatus
    severity: PredictionSeverity
    policy_id: Optional[str]
    opened_at: datetime
    closed_at: Optional[datetime]
    ack_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class FeatureUpsert(BaseModel):
    feature_name: str
    feature_value: float
    event_ts: datetime


class WellnessReadingCreate(BaseModel):
    athlete_id: UUID
    source: str
    metric: str
    value: float
    unit: Optional[str] = None
    event_ts: datetime
    quality_score: Optional[float] = None


class SessionListItem(BaseModel):
    session_id: UUID
    team_id: UUID
    type: SessionType
    start_ts: datetime
    end_ts: Optional[datetime]
    rpe_avg: Optional[float]
    load: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class SessionsPage(BaseModel):
    items: list[SessionListItem]
    page: int
    page_size: int
    total: int
    has_next: bool


class SessionParticipationItem(BaseModel):
    athlete_id: UUID
    rpe: Optional[float]
    load: Optional[float]
    status: SessionParticipationStatus

    class Config:
        from_attributes = True


class SessionDetail(BaseModel):
    session: SessionListItem
    participation: list[SessionParticipationItem]

    class Config:
        from_attributes = True


class WellnessMetricPoint(BaseModel):
    athlete_id: UUID
    metric: str
    value: float
    unit: Optional[str]
    event_ts: datetime

    class Config:
        from_attributes = True


class SnapshotPrediction(BaseModel):
    athlete_id: UUID
    score: float
    severity: PredictionSeverity
    model_version: str
    event_ts: datetime
    drivers: Optional[dict] = None

    class Config:
        from_attributes = True


class SnapshotAlert(BaseModel):
    id: UUID
    athlete_id: UUID
    session_id: Optional[UUID]
    status: AlertStatus
    severity: PredictionSeverity
    opened_at: datetime
    closed_at: Optional[datetime]
    policy_id: Optional[str]

    class Config:
        from_attributes = True


class SessionWellnessSnapshot(BaseModel):
    session_id: UUID
    window_days: int
    window_start: datetime
    window_end: datetime
    athletes: list[UUID]
    metrics: list[WellnessMetricPoint]
    predictions: list[SnapshotPrediction]
    alerts: list[SnapshotAlert]

    class Config:
        from_attributes = True


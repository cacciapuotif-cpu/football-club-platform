"""Schemas for performance modules (Technical, Tactical, Psychological, Health)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.performance import HealthStatus


# ============ Technical Stats ============
class TechnicalStatsBase(BaseModel):
    player_id: UUID
    date: date
    pass_accuracy_pct: float | None = Field(default=None, ge=0, le=100)
    shots_total: int | None = Field(default=None, ge=0)
    shots_on_target: int | None = Field(default=None, ge=0)
    goals: int | None = Field(default=None, ge=0)
    assists: int | None = Field(default=None, ge=0)
    dribbles_won: int | None = Field(default=None, ge=0)
    dribbles_attempted: int | None = Field(default=None, ge=0)
    duels_won: int | None = Field(default=None, ge=0)
    duels_lost: int | None = Field(default=None, ge=0)
    crosses_successful: int | None = Field(default=None, ge=0)
    crosses_attempted: int | None = Field(default=None, ge=0)
    unforced_errors: int | None = Field(default=None, ge=0)
    turnovers: int | None = Field(default=None, ge=0)
    weak_foot_usage_pct: float | None = Field(default=None, ge=0, le=100)
    decision_time_ms: float | None = Field(default=None, ge=0)
    heatmap_json: str | None = None


class TechnicalStatsCreate(TechnicalStatsBase):
    pass


class TechnicalStatsUpdate(BaseModel):
    date: Optional[date] = None
    pass_accuracy_pct: Optional[float] = None
    shots_total: Optional[int] = None
    shots_on_target: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    dribbles_won: Optional[int] = None
    dribbles_attempted: Optional[int] = None
    duels_won: Optional[int] = None
    duels_lost: Optional[int] = None
    crosses_successful: Optional[int] = None
    crosses_attempted: Optional[int] = None
    unforced_errors: Optional[int] = None
    turnovers: Optional[int] = None
    weak_foot_usage_pct: Optional[float] = None
    decision_time_ms: Optional[float] = None
    heatmap_json: Optional[str] = None


class TechnicalStatsResponse(TechnicalStatsBase):
    id: UUID
    organization_id: UUID
    conversion_rate_pct: float | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Tactical & Cognitive ============
class TacticalCognitiveBase(BaseModel):
    player_id: UUID
    date: date
    involvement_pct: float | None = Field(default=None, ge=0, le=100)
    reaction_time_ms: float | None = Field(default=None, ge=0)
    correct_decisions_pct: float | None = Field(default=None, ge=0, le=100)
    anticipations_pct: float | None = Field(default=None, ge=0, le=100)
    pressing_timing_ms: float | None = Field(default=None, ge=0)
    cognitive_errors: int | None = Field(default=None, ge=0)
    centroid_x_pct: float | None = Field(default=None, ge=0, le=100)
    centroid_y_pct: float | None = Field(default=None, ge=0, le=100)


class TacticalCognitiveCreate(TacticalCognitiveBase):
    pass


class TacticalCognitiveUpdate(BaseModel):
    date: Optional[date] = None
    involvement_pct: Optional[float] = None
    reaction_time_ms: Optional[float] = None
    correct_decisions_pct: Optional[float] = None
    anticipations_pct: Optional[float] = None
    pressing_timing_ms: Optional[float] = None
    cognitive_errors: Optional[int] = None
    centroid_x_pct: Optional[float] = None
    centroid_y_pct: Optional[float] = None


class TacticalCognitiveResponse(TacticalCognitiveBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Psychological Profile ============
class PsychologicalProfileBase(BaseModel):
    player_id: UUID
    date: date
    motivation_1_5: int | None = Field(default=None, ge=1, le=5)
    self_esteem_1_5: int | None = Field(default=None, ge=1, le=5)
    leadership_1_5: int | None = Field(default=None, ge=1, le=5)
    resilience_1_5: int | None = Field(default=None, ge=1, le=5)
    stress_mgmt_1_5: int | None = Field(default=None, ge=1, le=5)
    mental_fatigue_1_5: int | None = Field(default=None, ge=1, le=5)
    coach_note: str | None = Field(default=None, max_length=500)


class PsychologicalProfileCreate(PsychologicalProfileBase):
    pass


class PsychologicalProfileUpdate(BaseModel):
    date: Optional[date] = None
    motivation_1_5: Optional[int] = None
    self_esteem_1_5: Optional[int] = None
    leadership_1_5: Optional[int] = None
    resilience_1_5: Optional[int] = None
    stress_mgmt_1_5: Optional[int] = None
    mental_fatigue_1_5: Optional[int] = None
    coach_note: Optional[str] = None


class PsychologicalProfileResponse(PsychologicalProfileBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Health Monitoring ============
class HealthMonitoringBase(BaseModel):
    player_id: UUID
    week_start_date: date
    status: HealthStatus = HealthStatus.HEALTHY
    injury_type: str | None = Field(default=None, max_length=255)
    injury_start: date | None = None
    injury_end: date | None = None
    weekly_load_AU: float | None = Field(default=None, ge=0)
    injury_risk_0_1: float | None = Field(default=None, ge=0, le=1)
    avg_sleep_quality_1_5: float | None = Field(default=None, ge=1, le=5)
    nutrition_hydration_1_5: int | None = Field(default=None, ge=1, le=5)
    pain_1_10: int | None = Field(default=None, ge=1, le=10)


class HealthMonitoringCreate(HealthMonitoringBase):
    pass


class HealthMonitoringUpdate(BaseModel):
    week_start_date: Optional[date] = None
    status: Optional[HealthStatus] = None
    injury_type: Optional[str] = None
    injury_start: Optional[date] = None
    injury_end: Optional[date] = None
    weekly_load_AU: Optional[float] = None
    injury_risk_0_1: Optional[float] = None
    avg_sleep_quality_1_5: Optional[float] = None
    nutrition_hydration_1_5: Optional[int] = None
    pain_1_10: Optional[int] = None


class HealthMonitoringResponse(HealthMonitoringBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

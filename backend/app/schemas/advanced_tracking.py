"""Schemas for advanced tracking models."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.advanced_tracking import (
    GoalCategory,
    GoalStatus,
    InsightPriority,
    InsightType,
)


# ===== PerformanceSnapshot Schemas =====


class PerformanceSnapshotBase(BaseModel):
    """Base performance snapshot fields."""

    player_id: UUID
    snapshot_date: date
    period_type: str = Field(..., max_length=20)

    physical_score: float | None = Field(default=None, ge=0, le=100)
    technical_score: float | None = Field(default=None, ge=0, le=100)
    tactical_score: float | None = Field(default=None, ge=0, le=100)
    psychological_score: float | None = Field(default=None, ge=0, le=100)
    health_score: float | None = Field(default=None, ge=0, le=100)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    form_index: float | None = Field(default=None, ge=0, le=100)

    physical_percentile: float | None = Field(default=None, ge=0, le=100)
    technical_percentile: float | None = Field(default=None, ge=0, le=100)
    tactical_percentile: float | None = Field(default=None, ge=0, le=100)

    team_rank_physical: int | None = Field(default=None, ge=1)
    team_rank_technical: int | None = Field(default=None, ge=1)
    team_rank_overall: int | None = Field(default=None, ge=1)

    physical_zscore: float | None = None
    technical_zscore: float | None = None
    tactical_zscore: float | None = None

    trend_3m: int | None = Field(default=None, ge=-1, le=1)
    trend_6m: int | None = Field(default=None, ge=-1, le=1)

    metrics_summary: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class PerformanceSnapshotCreate(PerformanceSnapshotBase):
    """Schema for creating a performance snapshot."""

    pass


class PerformanceSnapshotUpdate(BaseModel):
    """Schema for updating a performance snapshot."""

    physical_score: Optional[float] = Field(default=None, ge=0, le=100)
    technical_score: Optional[float] = Field(default=None, ge=0, le=100)
    tactical_score: Optional[float] = Field(default=None, ge=0, le=100)
    psychological_score: Optional[float] = Field(default=None, ge=0, le=100)
    health_score: Optional[float] = Field(default=None, ge=0, le=100)
    overall_score: Optional[float] = Field(default=None, ge=0, le=100)
    form_index: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None


class PerformanceSnapshotResponse(PerformanceSnapshotBase):
    """Schema for performance snapshot response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ===== PlayerGoal Schemas =====


class PlayerGoalBase(BaseModel):
    """Base player goal fields."""

    player_id: UUID
    category: GoalCategory
    status: GoalStatus = GoalStatus.NOT_STARTED
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    metric_name: str = Field(..., max_length=100)
    baseline_value: float
    target_value: float
    current_value: float | None = None
    unit: str = Field(..., max_length=50)
    start_date: date
    target_date: date
    completed_date: date | None = None
    progress_pct: float = Field(default=0, ge=0, le=100)
    days_remaining: int | None = None
    on_track: bool | None = None
    milestones: str | None = None
    predicted_completion_probability: float | None = Field(default=None, ge=0, le=1)
    predicted_final_value: float | None = None
    assigned_by_user_id: UUID | None = None
    coach_notes: str | None = Field(default=None, max_length=500)


class PlayerGoalCreate(PlayerGoalBase):
    """Schema for creating a player goal."""

    pass


class PlayerGoalUpdate(BaseModel):
    """Schema for updating a player goal."""

    status: Optional[GoalStatus] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    current_value: Optional[float] = None
    target_date: Optional[date] = None
    completed_date: Optional[date] = None
    progress_pct: Optional[float] = Field(default=None, ge=0, le=100)
    on_track: Optional[bool] = None
    milestones: Optional[str] = None
    coach_notes: Optional[str] = None


class PlayerGoalResponse(PlayerGoalBase):
    """Schema for player goal response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== MatchPlayerStats Schemas =====


class MatchPlayerStatsBase(BaseModel):
    """Base match player stats fields."""

    player_id: UUID
    match_id: UUID
    match_date: date
    minutes_played: int = Field(..., ge=0, le=150)
    started: bool = False
    substituted_in_min: int | None = Field(default=None, ge=0, le=150)
    substituted_out_min: int | None = Field(default=None, ge=0, le=150)
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)

    # Physical
    distance_m: float | None = Field(default=None, ge=0)
    hi_distance_m: float | None = Field(default=None, ge=0)
    sprints_count: int | None = Field(default=None, ge=0)
    top_speed_kmh: float | None = Field(default=None, ge=0)
    accelerations: int | None = Field(default=None, ge=0)
    decelerations: int | None = Field(default=None, ge=0)

    # Technical
    passes_completed: int = Field(default=0, ge=0)
    passes_attempted: int = Field(default=0, ge=0)
    pass_accuracy_pct: float | None = Field(default=None, ge=0, le=100)
    key_passes: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    shots: int = Field(default=0, ge=0)
    shots_on_target: int = Field(default=0, ge=0)
    goals: int = Field(default=0, ge=0)
    dribbles_completed: int = Field(default=0, ge=0)
    dribbles_attempted: int = Field(default=0, ge=0)
    crosses_completed: int = Field(default=0, ge=0)
    crosses_attempted: int = Field(default=0, ge=0)

    # Defensive
    tackles: int = Field(default=0, ge=0)
    interceptions: int = Field(default=0, ge=0)
    clearances: int = Field(default=0, ge=0)
    blocks: int = Field(default=0, ge=0)
    duels_won: int = Field(default=0, ge=0)
    duels_lost: int = Field(default=0, ge=0)
    fouls_committed: int = Field(default=0, ge=0)
    fouls_won: int = Field(default=0, ge=0)

    # Advanced
    xg: float | None = Field(default=None, ge=0)
    xa: float | None = Field(default=None, ge=0)
    touches: int | None = Field(default=None, ge=0)
    possession_won: int | None = Field(default=None, ge=0)
    possession_lost: int | None = Field(default=None, ge=0)
    opponent_team: str | None = Field(default=None, max_length=255)
    opponent_difficulty: int | None = Field(default=None, ge=1, le=10)
    coach_rating: float | None = Field(default=None, ge=0, le=10)
    team_avg_rating: float | None = Field(default=None, ge=0, le=10)
    performance_index: float | None = Field(default=None, ge=0, le=100)
    stats_by_half: str | None = None
    heatmap_data: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class MatchPlayerStatsCreate(MatchPlayerStatsBase):
    """Schema for creating match player stats."""

    pass


class MatchPlayerStatsUpdate(BaseModel):
    """Schema for updating match player stats."""

    minutes_played: Optional[int] = Field(default=None, ge=0, le=150)
    goals: Optional[int] = Field(default=None, ge=0)
    assists: Optional[int] = Field(default=None, ge=0)
    yellow_cards: Optional[int] = Field(default=None, ge=0)
    red_cards: Optional[int] = Field(default=None, ge=0)
    coach_rating: Optional[float] = Field(default=None, ge=0, le=10)
    performance_index: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None


class MatchPlayerStatsResponse(MatchPlayerStatsBase):
    """Schema for match player stats response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ===== DailyReadiness Schemas =====


class DailyReadinessBase(BaseModel):
    """Base daily readiness fields."""

    player_id: UUID
    date: date
    readiness_score: float = Field(..., ge=0, le=100)
    sleep_score: float | None = Field(default=None, ge=0, le=100)
    hrv_score: float | None = Field(default=None, ge=0, le=100)
    recovery_score: float | None = Field(default=None, ge=0, le=100)
    wellness_score: float | None = Field(default=None, ge=0, le=100)
    workload_score: float | None = Field(default=None, ge=0, le=100)
    sleep_hours: float | None = None
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    hrv_ms: float | None = None
    resting_hr_bpm: int | None = Field(default=None, ge=30, le=220)
    doms_rating: int | None = Field(default=None, ge=1, le=5)
    fatigue_rating: int | None = Field(default=None, ge=1, le=5)
    stress_rating: int | None = Field(default=None, ge=1, le=5)
    mood_rating: int | None = Field(default=None, ge=1, le=10)
    yesterday_training_load: float | None = None
    acute_chronic_ratio: float | None = None
    recommended_training_intensity: str | None = Field(default=None, max_length=50)
    can_train_full: bool = True
    injury_risk_flag: bool = False
    predicted_performance_today: float | None = Field(default=None, ge=0, le=100)
    injury_risk_probability: float | None = Field(default=None, ge=0, le=1)
    coach_override: bool = False
    coach_override_reason: str | None = Field(default=None, max_length=500)


class DailyReadinessCreate(DailyReadinessBase):
    """Schema for creating daily readiness."""

    pass


class DailyReadinessUpdate(BaseModel):
    """Schema for updating daily readiness."""

    readiness_score: Optional[float] = Field(default=None, ge=0, le=100)
    recommended_training_intensity: Optional[str] = None
    can_train_full: Optional[bool] = None
    injury_risk_flag: Optional[bool] = None
    coach_override: Optional[bool] = None
    coach_override_reason: Optional[str] = None


class DailyReadinessResponse(DailyReadinessBase):
    """Schema for daily readiness response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ===== AutomatedInsight Schemas =====


class AutomatedInsightBase(BaseModel):
    """Base automated insight fields."""

    player_id: UUID | None = None
    team_id: UUID | None = None
    insight_type: InsightType
    priority: InsightPriority = InsightPriority.MEDIUM
    category: str = Field(..., max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    actionable_recommendation: str | None = None
    supporting_data: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    statistical_significance: float | None = None
    date_from: date | None = None
    date_to: date | None = None
    comparison_baseline: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_read: bool = False
    read_at: datetime | None = None
    read_by_user_id: UUID | None = None
    dismissed: bool = False
    coach_feedback: str | None = Field(default=None, max_length=500)
    was_helpful: bool | None = None


class AutomatedInsightCreate(AutomatedInsightBase):
    """Schema for creating automated insight."""

    pass


class AutomatedInsightUpdate(BaseModel):
    """Schema for updating automated insight."""

    is_active: Optional[bool] = None
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    read_by_user_id: Optional[UUID] = None
    dismissed: Optional[bool] = None
    coach_feedback: Optional[str] = None
    was_helpful: Optional[bool] = None


class AutomatedInsightResponse(AutomatedInsightBase):
    """Schema for automated insight response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

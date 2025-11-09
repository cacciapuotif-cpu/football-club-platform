"""Pydantic schemas for API validation and responses."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.enums import (
    PlayerRole, DominantFoot, SessionType, PitchType,
    TimeOfDay, PlayerStatus
)


# ===== PLAYER SCHEMAS =====

class PlayerBase(BaseModel):
    """Base player schema."""
    code: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    category: str = Field(..., min_length=1, max_length=50)
    primary_role: PlayerRole = PlayerRole.MF
    secondary_role: Optional[PlayerRole] = None
    dominant_foot: DominantFoot = DominantFoot.RIGHT
    shirt_number: Optional[int] = Field(None, ge=1, le=99)
    years_active: int = Field(default=0, ge=0)


class PlayerCreate(PlayerBase):
    """Schema for creating a player."""
    pass


class PlayerUpdate(BaseModel):
    """Schema for updating a player."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    primary_role: Optional[PlayerRole] = None
    secondary_role: Optional[PlayerRole] = None
    dominant_foot: Optional[DominantFoot] = None
    shirt_number: Optional[int] = Field(None, ge=1, le=99)
    years_active: Optional[int] = Field(None, ge=0)


class PlayerResponse(PlayerBase):
    """Schema for player response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== METRICS SCHEMAS =====

class MetricsPhysicalBase(BaseModel):
    """Base physical metrics schema."""
    height_cm: Optional[Decimal] = Field(None, ge=100, le=250)
    weight_kg: Optional[Decimal] = Field(None, ge=30, le=150)
    body_fat_pct: Optional[Decimal] = Field(None, ge=0, le=50)
    lean_mass_kg: Optional[Decimal] = Field(None, ge=20, le=120)
    resting_hr_bpm: int = Field(..., ge=30, le=120)
    max_speed_kmh: Optional[Decimal] = Field(None, ge=0, le=50)
    accel_0_10m_s: Optional[Decimal] = Field(None, ge=0, le=5)
    accel_0_20m_s: Optional[Decimal] = Field(None, ge=0, le=10)
    distance_km: Decimal = Field(..., ge=0, le=25)
    sprints_over_25kmh: int = Field(default=0, ge=0, le=200)
    vertical_jump_cm: Optional[Decimal] = Field(None, ge=0, le=100)
    agility_illinois_s: Optional[Decimal] = Field(None, ge=10, le=30)
    yoyo_level: Optional[Decimal] = Field(None, ge=0, le=30)
    rpe: Decimal = Field(..., ge=1, le=10)
    sleep_hours: Optional[Decimal] = Field(None, ge=0, le=12)


class MetricsPhysicalCreate(MetricsPhysicalBase):
    """Schema for creating physical metrics."""
    pass


class MetricsPhysicalResponse(MetricsPhysicalBase):
    """Schema for physical metrics response."""
    id: UUID
    session_id: UUID
    bmi: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class MetricsTechnicalBase(BaseModel):
    """Base technical metrics schema."""
    passes_attempted: int = Field(default=0, ge=0, le=500)
    passes_completed: int = Field(default=0, ge=0, le=500)
    progressive_passes: int = Field(default=0, ge=0, le=100)
    long_pass_accuracy_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    shots: int = Field(default=0, ge=0, le=50)
    shots_on_target: int = Field(default=0, ge=0, le=50)
    crosses: Optional[int] = Field(default=0, ge=0, le=50)
    cross_accuracy_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    successful_dribbles: int = Field(default=0, ge=0, le=100)
    failed_dribbles: int = Field(default=0, ge=0, le=100)
    ball_losses: int = Field(default=0, ge=0, le=100)
    ball_recoveries: int = Field(default=0, ge=0, le=100)
    set_piece_accuracy_pct: Optional[Decimal] = Field(None, ge=0, le=100)

    @field_validator('passes_completed')
    @classmethod
    def validate_passes_completed(cls, v, info):
        """Validate that passes_completed <= passes_attempted."""
        if 'passes_attempted' in info.data and v > info.data['passes_attempted']:
            raise ValueError('passes_completed cannot exceed passes_attempted')
        return v

    @field_validator('shots_on_target')
    @classmethod
    def validate_shots_on_target(cls, v, info):
        """Validate that shots_on_target <= shots."""
        if 'shots' in info.data and v > info.data['shots']:
            raise ValueError('shots_on_target cannot exceed shots')
        return v


class MetricsTechnicalCreate(MetricsTechnicalBase):
    """Schema for creating technical metrics."""
    pass


class MetricsTechnicalResponse(MetricsTechnicalBase):
    """Schema for technical metrics response."""
    id: UUID
    session_id: UUID
    pass_accuracy_pct: Optional[Decimal] = None
    shot_accuracy_pct: Optional[Decimal] = None
    dribble_success_pct: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class MetricsTacticalBase(BaseModel):
    """Base tactical metrics schema."""
    xg: Optional[Decimal] = Field(None, ge=0, le=10)
    xa: Optional[Decimal] = Field(None, ge=0, le=10)
    pressures: Optional[int] = Field(default=0, ge=0, le=200)
    interceptions: int = Field(default=0, ge=0, le=50)
    heatmap_zone_json: Optional[Dict[str, Any]] = None
    influence_zones_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_off_ball_runs: Optional[int] = Field(default=0, ge=0, le=100)
    transition_reaction_time_s: Optional[Decimal] = Field(None, ge=0, le=10)
    involvement_pct: Optional[Decimal] = Field(None, ge=0, le=100)


class MetricsTacticalCreate(MetricsTacticalBase):
    """Schema for creating tactical metrics."""
    pass


class MetricsTacticalResponse(MetricsTacticalBase):
    """Schema for tactical metrics response."""
    id: UUID
    session_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MetricsPsychBase(BaseModel):
    """Base psychological metrics schema."""
    attention_score: Optional[int] = Field(None, ge=0, le=100)
    decision_making: Optional[int] = Field(None, ge=1, le=10)
    motivation: Optional[int] = Field(None, ge=1, le=10)
    stress_management: Optional[int] = Field(None, ge=1, le=10)
    self_esteem: Optional[int] = Field(None, ge=1, le=10)
    team_leadership: Optional[int] = Field(None, ge=1, le=10)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    mood_pre: Optional[int] = Field(None, ge=1, le=10)
    mood_post: Optional[int] = Field(None, ge=1, le=10)
    tactical_adaptability: Optional[int] = Field(None, ge=1, le=10)


class MetricsPsychCreate(MetricsPsychBase):
    """Schema for creating psychological metrics."""
    pass


class MetricsPsychResponse(MetricsPsychBase):
    """Schema for psychological metrics response."""
    id: UUID
    session_id: UUID

    model_config = ConfigDict(from_attributes=True)


class AnalyticsOutputsResponse(BaseModel):
    """Schema for analytics outputs response."""
    id: UUID
    session_id: UUID
    performance_index: Decimal
    progress_index_rolling: Optional[Decimal] = None
    zscore_vs_player_baseline: Optional[Decimal] = None
    cluster_label: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== SESSION SCHEMAS =====

class SessionBase(BaseModel):
    """Base session schema."""
    session_date: date
    session_type: SessionType
    minutes_played: int = Field(default=0, ge=0, le=180)
    coach_rating: Optional[Decimal] = Field(None, ge=0, le=10)
    match_score: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    pitch_type: Optional[PitchType] = None
    weather: Optional[str] = Field(None, max_length=100)
    time_of_day: Optional[TimeOfDay] = None
    status: PlayerStatus = PlayerStatus.OK


class SessionCreate(BaseModel):
    """Schema for creating a session with nested metrics."""
    player_code: str
    session: SessionBase
    metrics_physical: MetricsPhysicalCreate
    metrics_technical: MetricsTechnicalCreate
    metrics_tactical: MetricsTacticalCreate
    metrics_psych: MetricsPsychCreate


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    session_date: Optional[date] = None
    session_type: Optional[SessionType] = None
    minutes_played: Optional[int] = Field(None, ge=0, le=180)
    coach_rating: Optional[Decimal] = Field(None, ge=0, le=10)
    match_score: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    pitch_type: Optional[PitchType] = None
    weather: Optional[str] = Field(None, max_length=100)
    time_of_day: Optional[TimeOfDay] = None
    status: Optional[PlayerStatus] = None


class SessionResponse(SessionBase):
    """Schema for session response with all metrics."""
    id: UUID
    player_id: UUID
    created_at: datetime
    updated_at: datetime
    metrics_physical: Optional[MetricsPhysicalResponse] = None
    metrics_technical: Optional[MetricsTechnicalResponse] = None
    metrics_tactical: Optional[MetricsTacticalResponse] = None
    metrics_psych: Optional[MetricsPsychResponse] = None
    analytics_outputs: Optional[AnalyticsOutputsResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ===== ANALYTICS SCHEMAS =====

class PlayerTrendResponse(BaseModel):
    """Schema for player trend analytics."""
    session_date: date
    performance_index: Decimal
    progress_index_rolling: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    pass_accuracy_pct: Optional[Decimal] = None
    progressive_passes: Optional[int] = None
    interceptions: Optional[int] = None
    successful_dribbles: Optional[int] = None
    sprints_over_25kmh: Optional[int] = None
    rpe: Optional[Decimal] = None
    coach_rating: Optional[Decimal] = None


class PlayerSummaryResponse(BaseModel):
    """Schema for player summary analytics."""
    player_id: UUID
    player_name: str
    total_sessions: int
    avg_performance_index: Decimal
    max_performance_index: Decimal
    min_performance_index: Decimal
    current_baseline_zscore: Optional[Decimal] = None
    training_stats: Dict[str, Any]
    match_stats: Dict[str, Any]


class PlayerCompareResponse(BaseModel):
    """Schema for comparing multiple players."""
    player_id: UUID
    player_name: str
    avg_performance_index: Decimal
    recent_sessions_count: int
    key_metrics: Dict[str, Any]

"""Advanced tracking models for player performance and development."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class GoalStatus(str, Enum):
    """Player goal status."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GoalCategory(str, Enum):
    """Goal category types."""

    PHYSICAL = "PHYSICAL"
    TECHNICAL = "TECHNICAL"
    TACTICAL = "TACTICAL"
    PSYCHOLOGICAL = "PSYCHOLOGICAL"
    HEALTH = "HEALTH"


class InsightPriority(str, Enum):
    """Insight priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InsightType(str, Enum):
    """Types of automated insights."""

    PERFORMANCE_DROP = "PERFORMANCE_DROP"
    PERFORMANCE_PEAK = "PERFORMANCE_PEAK"
    INJURY_RISK = "INJURY_RISK"
    WELLNESS_ALERT = "WELLNESS_ALERT"
    GOAL_PROGRESS = "GOAL_PROGRESS"
    TRAINING_LOAD = "TRAINING_LOAD"
    TECHNICAL_IMPROVEMENT = "TECHNICAL_IMPROVEMENT"
    TACTICAL_IMPROVEMENT = "TACTICAL_IMPROVEMENT"
    COMPARISON = "COMPARISON"


class PerformanceSnapshot(SQLModel, table=True):
    """
    Periodic performance snapshot with aggregated metrics and trends.
    Captures weekly/monthly player state for longitudinal tracking.
    """

    __tablename__ = "performance_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    snapshot_date: date
    period_type: str = Field(max_length=20)  # WEEKLY, MONTHLY, QUARTERLY

    # Aggregated scores (0-100)
    physical_score: float | None = Field(default=None, ge=0, le=100)
    technical_score: float | None = Field(default=None, ge=0, le=100)
    tactical_score: float | None = Field(default=None, ge=0, le=100)
    psychological_score: float | None = Field(default=None, ge=0, le=100)
    health_score: float | None = Field(default=None, ge=0, le=100)
    overall_score: float | None = Field(default=None, ge=0, le=100)

    # Form index (recent 4 weeks weighted average)
    form_index: float | None = Field(default=None, ge=0, le=100)

    # Percentiles vs personal history
    physical_percentile: float | None = Field(default=None, ge=0, le=100)
    technical_percentile: float | None = Field(default=None, ge=0, le=100)
    tactical_percentile: float | None = Field(default=None, ge=0, le=100)

    # Percentiles vs team
    team_rank_physical: int | None = Field(default=None, ge=1)
    team_rank_technical: int | None = Field(default=None, ge=1)
    team_rank_overall: int | None = Field(default=None, ge=1)

    # Z-scores vs baseline
    physical_zscore: float | None = None
    technical_zscore: float | None = None
    tactical_zscore: float | None = None

    # Trend indicators (-1: declining, 0: stable, 1: improving)
    trend_3m: int | None = Field(default=None, ge=-1, le=1)
    trend_6m: int | None = Field(default=None, ge=-1, le=1)

    # Key metrics summary (JSON)
    metrics_summary: str | None = Field(default=None, sa_column=Column(Text))

    # Notes
    notes: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class PlayerGoal(SQLModel, table=True):
    """
    SMART goals for player development with progress tracking.
    Supports specific, measurable, achievable, relevant, time-bound objectives.
    """

    __tablename__ = "player_goals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    category: GoalCategory
    status: GoalStatus = Field(default=GoalStatus.NOT_STARTED)

    # SMART criteria
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text))
    metric_name: str = Field(max_length=100)  # e.g., "pass_accuracy_pct"
    baseline_value: float  # Starting value
    target_value: float  # Goal to achieve
    current_value: float | None = None  # Latest measurement
    unit: str = Field(max_length=50)  # %, seconds, meters, etc.

    # Timeline
    start_date: date
    target_date: date
    completed_date: date | None = None

    # Progress tracking
    progress_pct: float = Field(default=0, ge=0, le=100)
    days_remaining: int | None = None
    on_track: bool | None = None  # ML predicted likelihood

    # Milestones (JSON array of intermediate targets)
    milestones: str | None = Field(default=None, sa_column=Column(Text))

    # ML prediction
    predicted_completion_probability: float | None = Field(default=None, ge=0, le=1)
    predicted_final_value: float | None = None

    # Assignment
    assigned_by_user_id: UUID | None = Field(default=None, foreign_key="users.id")
    coach_notes: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True


class MatchPlayerStats(SQLModel, table=True):
    """
    Detailed match-specific player statistics.
    Separates match performance from training sessions.
    """

    __tablename__ = "match_player_stats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    match_id: UUID = Field(foreign_key="matches.id", index=True)
    match_date: date

    # Playing time
    minutes_played: int = Field(ge=0, le=150)  # Including extra time
    started: bool = Field(default=False)
    substituted_in_min: int | None = Field(default=None, ge=0, le=150)
    substituted_out_min: int | None = Field(default=None, ge=0, le=150)

    # Disciplinary
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)

    # Physical (from GPS)
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

    # Advanced metrics
    xg: float | None = Field(default=None, ge=0)  # Expected goals
    xa: float | None = Field(default=None, ge=0)  # Expected assists
    touches: int | None = Field(default=None, ge=0)
    possession_won: int | None = Field(default=None, ge=0)
    possession_lost: int | None = Field(default=None, ge=0)

    # Performance vs opponent
    opponent_team: str | None = Field(default=None, max_length=255)
    opponent_difficulty: int | None = Field(default=None, ge=1, le=10)

    # Ratings
    coach_rating: float | None = Field(default=None, ge=0, le=10)
    team_avg_rating: float | None = Field(default=None, ge=0, le=10)
    performance_index: float | None = Field(default=None, ge=0, le=100)

    # Per-half breakdown (JSON)
    stats_by_half: str | None = Field(default=None, sa_column=Column(Text))

    # Position heatmap (JSON coordinates)
    heatmap_data: str | None = Field(default=None, sa_column=Column(Text))

    # Notes
    notes: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class DailyReadiness(SQLModel, table=True):
    """
    Daily readiness score predicting optimal training capacity.
    Integrates wellness, recovery, and workload data.
    """

    __tablename__ = "daily_readiness"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: date

    # Overall readiness score (0-100)
    readiness_score: float = Field(ge=0, le=100)

    # Component scores (0-100 each)
    sleep_score: float | None = Field(default=None, ge=0, le=100)
    hrv_score: float | None = Field(default=None, ge=0, le=100)
    recovery_score: float | None = Field(default=None, ge=0, le=100)
    wellness_score: float | None = Field(default=None, ge=0, le=100)
    workload_score: float | None = Field(default=None, ge=0, le=100)

    # Raw input metrics
    sleep_hours: float | None = None
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    hrv_ms: float | None = None
    resting_hr_bpm: int | None = Field(default=None, ge=30, le=220)
    doms_rating: int | None = Field(default=None, ge=1, le=5)
    fatigue_rating: int | None = Field(default=None, ge=1, le=5)
    stress_rating: int | None = Field(default=None, ge=1, le=5)
    mood_rating: int | None = Field(default=None, ge=1, le=10)
    yesterday_training_load: float | None = None
    acute_chronic_ratio: float | None = None  # ACWR

    # Recommendations
    recommended_training_intensity: str | None = Field(
        default=None, max_length=50
    )  # LOW, MODERATE, HIGH, MAX
    can_train_full: bool = Field(default=True)
    injury_risk_flag: bool = Field(default=False)

    # ML model predictions
    predicted_performance_today: float | None = Field(default=None, ge=0, le=100)
    injury_risk_probability: float | None = Field(default=None, ge=0, le=1)

    # Coach override
    coach_override: bool = Field(default=False)
    coach_override_reason: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class AutomatedInsight(SQLModel, table=True):
    """
    AI-generated insights about player performance and development.
    Automatically identifies patterns, anomalies, and opportunities.
    """

    __tablename__ = "automated_insights"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID | None = Field(default=None, foreign_key="players.id", index=True)
    team_id: UUID | None = Field(default=None, foreign_key="teams.id", index=True)

    # Insight classification
    insight_type: InsightType
    priority: InsightPriority = Field(default=InsightPriority.MEDIUM)
    category: str = Field(max_length=50)  # PERFORMANCE, WELLNESS, INJURY, GOAL, etc.

    # Content
    title: str = Field(max_length=255)
    description: str = Field(sa_column=Column(Text))
    actionable_recommendation: str | None = Field(default=None, sa_column=Column(Text))

    # Metrics & evidence (JSON)
    supporting_data: str | None = Field(default=None, sa_column=Column(Text))

    # Statistical significance
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    statistical_significance: float | None = None  # p-value

    # Context
    date_from: date | None = None
    date_to: date | None = None
    comparison_baseline: str | None = Field(default=None, max_length=255)

    # Lifecycle
    is_active: bool = Field(default=True)
    is_read: bool = Field(default=False)
    read_at: datetime | None = None
    read_by_user_id: UUID | None = Field(default=None, foreign_key="users.id")
    dismissed: bool = Field(default=False)

    # Coach feedback
    coach_feedback: str | None = Field(default=None, max_length=500)
    was_helpful: bool | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True

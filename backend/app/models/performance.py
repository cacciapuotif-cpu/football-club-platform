"""Performance tracking models: Technical, Tactical, Psychological, Health."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class HealthStatus(str, Enum):
    """Player health status."""

    HEALTHY = "HEALTHY"
    INJURED = "INJURED"
    RECOVERING = "RECOVERING"
    ILLNESS = "ILLNESS"


class TechnicalStats(SQLModel, table=True):
    """
    Technical performance statistics from matches/training.
    Tracks passing, shooting, dribbling, and other technical metrics.
    """

    __tablename__ = "technical_stats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: date

    # Passing
    pass_accuracy_pct: float | None = Field(default=None, ge=0, le=100)

    # Shooting
    shots_total: int | None = Field(default=None, ge=0)
    shots_on_target: int | None = Field(default=None, ge=0)
    goals: int | None = Field(default=None, ge=0)
    assists: int | None = Field(default=None, ge=0)
    conversion_rate_pct: float | None = Field(default=None, ge=0, le=100)  # Auto-calculated

    # Dribbling
    dribbles_won: int | None = Field(default=None, ge=0)
    dribbles_attempted: int | None = Field(default=None, ge=0)

    # Duels
    duels_won: int | None = Field(default=None, ge=0)
    duels_lost: int | None = Field(default=None, ge=0)

    # Crosses
    crosses_successful: int | None = Field(default=None, ge=0)
    crosses_attempted: int | None = Field(default=None, ge=0)

    # Errors
    unforced_errors: int | None = Field(default=None, ge=0)
    turnovers: int | None = Field(default=None, ge=0)

    # Decision making
    weak_foot_usage_pct: float | None = Field(default=None, ge=0, le=100)
    decision_time_ms: float | None = Field(default=None, ge=0)

    # Positional (optional heatmap JSON)
    heatmap_json: str | None = Field(default=None, sa_column=Column(Text))

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class TacticalCognitive(SQLModel, table=True):
    """
    Tactical and cognitive performance assessment.
    Tracks positioning, decision-making, and tactical awareness.
    """

    __tablename__ = "tactical_cognitive"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: date

    # Participation & Involvement
    involvement_pct: float | None = Field(default=None, ge=0, le=100)

    # Cognitive metrics
    reaction_time_ms: float | None = Field(default=None, ge=0)
    correct_decisions_pct: float | None = Field(default=None, ge=0, le=100)
    anticipations_pct: float | None = Field(default=None, ge=0, le=100)
    pressing_timing_ms: float | None = Field(default=None, ge=0)
    cognitive_errors: int | None = Field(default=None, ge=0)

    # Positioning (normalized 0-100 for field coordinates)
    centroid_x_pct: float | None = Field(default=None, ge=0, le=100)
    centroid_y_pct: float | None = Field(default=None, ge=0, le=100)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class PsychologicalProfile(SQLModel, table=True):
    """
    Psychological profile assessment.
    Tracks mental state, motivation, and emotional well-being (1-5 Likert scale).
    """

    __tablename__ = "psychological_profile"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: date

    # Psychological metrics (1-5 Likert scale)
    motivation_1_5: int | None = Field(default=None, ge=1, le=5)
    self_esteem_1_5: int | None = Field(default=None, ge=1, le=5)
    leadership_1_5: int | None = Field(default=None, ge=1, le=5)
    resilience_1_5: int | None = Field(default=None, ge=1, le=5)
    stress_mgmt_1_5: int | None = Field(default=None, ge=1, le=5)
    mental_fatigue_1_5: int | None = Field(default=None, ge=1, le=5)

    # Coach/psychologist notes
    coach_note: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class HealthMonitoring(SQLModel, table=True):
    """
    Health and injury monitoring.
    Tracks injury status, risk indicators, and overall health metrics.
    """

    __tablename__ = "health_monitoring"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    week_start_date: date

    # Health status
    status: HealthStatus = Field(default=HealthStatus.HEALTHY)
    injury_type: str | None = Field(default=None, max_length=255)
    injury_start: date | None = Field(default=None)
    injury_end: date | None = Field(default=None)

    # Weekly aggregates
    weekly_load_AU: float | None = Field(default=None, ge=0)  # Arbitrary Units
    injury_risk_0_1: float | None = Field(default=None, ge=0, le=1)

    # Average wellness metrics for the week
    avg_sleep_quality_1_5: float | None = Field(default=None, ge=1, le=5)
    nutrition_hydration_1_5: int | None = Field(default=None, ge=1, le=5)

    # Pain level (1-10)
    pain_1_10: int | None = Field(default=None, ge=1, le=10)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True

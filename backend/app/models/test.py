"""Physical, Technical, Tactical, Wellness test models."""

from datetime import datetime, date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class PhysicalTest(SQLModel, table=True):
    """Physical/conditional test results."""

    __tablename__ = "physical_tests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    test_date: date
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Anthropometric
    height_cm: float | None = None
    weight_kg: float | None = None
    bmi: float | None = None
    body_fat_pct: float | None = None
    lean_mass_kg: float | None = None

    # Aerobic
    vo2max_ml_kg_min: float | None = None
    cooper_test_m: float | None = None
    yoyo_test_level: float | None = None
    vam_km_h: float | None = None

    # Anaerobic/Speed
    sprint_10m_s: float | None = None
    sprint_20m_s: float | None = None
    sprint_30m_s: float | None = None
    rsa_best_s: float | None = None
    cod_505_s: float | None = None
    illinois_s: float | None = None

    # Power
    cmj_cm: float | None = None
    sj_cm: float | None = None
    cmj_left_cm: float | None = None
    cmj_right_cm: float | None = None

    # Mobility
    sit_and_reach_cm: float | None = None
    ankle_dorsiflexion_deg: float | None = None
    fms_score: int | None = None  # 0-21

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Notes
    notes: str | None = Field(default=None, sa_column=Column(Text))
    tester_name: str | None = Field(default=None, max_length=255)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class TechnicalTest(SQLModel, table=True):
    """Technical skills test."""

    __tablename__ = "technical_tests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    test_date: date
    player_id: UUID = Field(foreign_key="players.id", index=True)
    match_id: UUID | None = Field(default=None, foreign_key="matches.id")

    # Passing
    passes_completed: int | None = None
    passes_attempted: int | None = None
    passing_accuracy_pct: float | None = None
    progressive_passes: int | None = None

    # Dribbling
    dribbles_completed: int | None = None
    dribbles_attempted: int | None = None
    dribbling_success_pct: float | None = None

    # Shooting
    shots_on_target: int | None = None
    shots_attempted: int | None = None
    shooting_accuracy_pct: float | None = None
    goals: int | None = None

    # Crosses
    crosses_completed: int | None = None
    crosses_attempted: int | None = None

    # Duels
    duels_won: int | None = None
    duels_total: int | None = None
    duels_win_pct: float | None = None

    # First touch
    first_touch_success: int | None = None
    first_touch_attempts: int | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    notes: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class TacticalTest(SQLModel, table=True):
    """Tactical/cognitive assessment."""

    __tablename__ = "tactical_tests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    test_date: date
    player_id: UUID = Field(foreign_key="players.id", index=True)
    match_id: UUID | None = Field(default=None, foreign_key="matches.id")

    # Positioning
    avg_position_x: float | None = None  # Normalized 0-1
    avg_position_y: float | None = None
    position_variance: float | None = None

    # Defensive
    recoveries: int | None = None
    interceptions: int | None = None
    clearances: int | None = None
    pressing_actions: int | None = None

    # Decision making
    decision_making_rating: float | None = None  # 1-10
    attention_rating: float | None = None
    anticipation_rating: float | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    notes: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


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

"""Player Training Statistics - Detailed performance tracking for individual training sessions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, Text
from sqlalchemy import func, Index

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.session import TrainingSession


class PlayerTrainingStats(SQLModel, table=True):
    """
    Detailed player statistics for each training session.
    Tracks technical, tactical, physical, and mental performance during training.
    """

    __tablename__ = "player_training_stats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    training_session_id: UUID = Field(foreign_key="training_sessions.id", index=True)

    # Attendance & Participation
    attendance: bool = Field(default=True)
    participation_pct: float = Field(default=100.0, ge=0, le=100)  # % of session completed
    late_arrival_min: int = Field(default=0, ge=0)

    # ============================================
    # TECHNICAL RATINGS (1-10 scale)
    # ============================================
    technical_rating: int = Field(default=5, ge=1, le=10)  # Overall technical execution
    tactical_execution: int = Field(default=5, ge=1, le=10)  # Following tactical instructions
    physical_performance: int = Field(default=5, ge=1, le=10)  # Physical output
    mental_focus: int = Field(default=5, ge=1, le=10)  # Concentration and attitude

    # ============================================
    # TECHNICAL METRICS (Percentages)
    # ============================================
    passing_accuracy: float = Field(default=0.0, ge=0, le=100)  # % successful passes
    shooting_accuracy: float = Field(default=0.0, ge=0, le=100)  # % on target
    dribbling_success: float = Field(default=0.0, ge=0, le=100)  # % successful dribbles
    first_touch_quality: float = Field(default=0.0, ge=0, le=100)  # % good first touches
    defensive_actions: int = Field(default=0, ge=0)  # Tackles, interceptions, etc.

    # ============================================
    # PHYSICAL METRICS MEASURED
    # ============================================
    speed_kmh: float | None = Field(default=None, ge=0)  # Top speed
    endurance_index: float | None = Field(default=None, ge=0, le=100)  # Stamina level
    recovery_rate: float | None = Field(default=None, ge=0, le=100)  # Recovery between drills
    distance_covered_m: float | None = Field(default=None, ge=0)  # Total meters
    hi_intensity_runs: int | None = Field(default=None, ge=0)  # High intensity runs count
    sprints_count: int | None = Field(default=None, ge=0)  # Number of sprints

    # ============================================
    # FITNESS & CONDITIONING
    # ============================================
    aerobic_capacity: float | None = Field(default=None, ge=0, le=100)  # VO2 max estimate
    power_output: float | None = Field(default=None, ge=0)  # Watt or normalized
    agility_score: float | None = Field(default=None, ge=0, le=100)  # Agility drill performance
    strength_score: float | None = Field(default=None, ge=0, le=100)  # Strength exercises

    # ============================================
    # WELLNESS & RPE
    # ============================================
    rpe_score: int | None = Field(default=None, ge=1, le=10)  # Rate of Perceived Exertion
    fatigue_level: int | None = Field(default=None, ge=1, le=10)  # 1=fresh, 10=exhausted
    muscle_soreness: int | None = Field(default=None, ge=1, le=10)  # 1=none, 10=severe
    sleep_quality: int | None = Field(default=None, ge=1, le=10)  # Self-reported
    hydration_level: int | None = Field(default=None, ge=1, le=10)  # 1=dehydrated, 10=optimal

    # ============================================
    # COACH FEEDBACK & NOTES
    # ============================================
    coach_feedback: str | None = Field(default=None, sa_column=Column(Text))
    areas_to_improve: str | None = Field(default=None, sa_column=Column(Text))
    positive_notes: str | None = Field(default=None, sa_column=Column(Text))

    # Coach ratings
    attitude_rating: int = Field(default=5, ge=1, le=10)  # Work ethic, commitment
    teamwork_rating: int = Field(default=5, ge=1, le=10)  # Cooperation with teammates

    # ============================================
    # INJURY & RISK MONITORING
    # ============================================
    injury_concern: bool = Field(default=False)
    injury_notes: str | None = Field(default=None, max_length=500)
    recommended_rest: bool = Field(default=False)

    # ============================================
    # ML COMPUTED METRICS
    # ============================================
    training_load_score: float | None = Field(default=None, ge=0, le=100)  # Calculated training load
    performance_trend: str | None = Field(default=None, max_length=20)  # improving, stable, declining
    predicted_match_readiness: float | None = Field(default=None, ge=0, le=100)  # % ready for match

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    player: Optional["Player"] = Relationship(back_populates="training_stats")

    __table_args__ = (
        Index("idx_player_training_player_session", "player_id", "training_session_id"),
        Index("idx_player_training_org", "organization_id"),
    )

    def calculate_overall_session_score(self) -> float:
        """Calculate an overall session score based on all ratings."""
        weights = {
            'technical': 0.3,
            'tactical': 0.25,
            'physical': 0.25,
            'mental': 0.2
        }

        score = (
            self.technical_rating * weights['technical'] +
            self.tactical_execution * weights['tactical'] +
            self.physical_performance * weights['physical'] +
            self.mental_focus * weights['mental']
        )

        return round(score, 2)

    class Config:
        use_enum_values = True

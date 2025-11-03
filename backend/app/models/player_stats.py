"""Comprehensive player statistics model for match/session tracking."""

from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func, Index

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.match import Match
    from app.models.session import Session


class PlayerStats(SQLModel, table=True):
    """
    Comprehensive player statistics for each match/session.
    Tracks offensive, defensive, passing, physical metrics and ML-computed scores.
    """

    __tablename__ = "player_stats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    match_id: UUID | None = Field(default=None, foreign_key="matches.id", index=True)
    session_id: UUID | None = Field(default=None, foreign_key="training_sessions.id", index=True)

    season: str = Field(max_length=20, index=True)  # e.g., "2024-2025"
    date: date
    minutes_played: int = Field(default=0, ge=0, le=120)

    # ============================================
    # OFFENSIVE STATISTICS
    # ============================================
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    shots: int = Field(default=0, ge=0)
    shots_on_target: int = Field(default=0, ge=0)
    dribbles_attempted: int = Field(default=0, ge=0)
    dribbles_success: int = Field(default=0, ge=0)
    offsides: int = Field(default=0, ge=0)
    penalties_scored: int = Field(default=0, ge=0)
    penalties_missed: int = Field(default=0, ge=0)

    # ============================================
    # PASSING STATISTICS
    # ============================================
    passes_attempted: int = Field(default=0, ge=0)
    passes_completed: int = Field(default=0, ge=0)
    key_passes: int = Field(default=0, ge=0)
    through_balls: int = Field(default=0, ge=0)
    crosses: int = Field(default=0, ge=0)
    cross_accuracy_pct: float = Field(default=0.0, ge=0, le=100)
    long_balls: int = Field(default=0, ge=0)
    long_balls_completed: int = Field(default=0, ge=0)

    # ============================================
    # DEFENSIVE STATISTICS
    # ============================================
    tackles_attempted: int = Field(default=0, ge=0)
    tackles_success: int = Field(default=0, ge=0)
    interceptions: int = Field(default=0, ge=0)
    clearances: int = Field(default=0, ge=0)
    blocks: int = Field(default=0, ge=0)
    aerial_duels_won: int = Field(default=0, ge=0)
    aerial_duels_lost: int = Field(default=0, ge=0)
    duels_won: int = Field(default=0, ge=0)
    duels_lost: int = Field(default=0, ge=0)

    # ============================================
    # GOALKEEPER STATISTICS (if applicable)
    # ============================================
    saves: int = Field(default=0, ge=0)
    saves_from_inside_box: int = Field(default=0, ge=0)
    punches: int = Field(default=0, ge=0)
    high_claims: int = Field(default=0, ge=0)
    catches: int = Field(default=0, ge=0)
    sweeper_clearances: int = Field(default=0, ge=0)
    throw_outs: int = Field(default=0, ge=0)
    goal_kicks: int = Field(default=0, ge=0)

    # ============================================
    # PHYSICAL & DISCIPLINE
    # ============================================
    distance_covered_m: int = Field(default=0, ge=0)  # meters
    sprints: int = Field(default=0, ge=0)
    top_speed_kmh: float = Field(default=0.0, ge=0)
    fouls_committed: int = Field(default=0, ge=0)
    fouls_suffered: int = Field(default=0, ge=0)
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)

    # ============================================
    # ML COMPUTED METRICS
    # ============================================
    performance_index: float = Field(default=0.0, ge=0, le=100)
    influence_score: float = Field(default=0.0, ge=0, le=10)
    expected_goals_xg: float = Field(default=0.0, ge=0)
    expected_assists_xa: float = Field(default=0.0, ge=0)

    # Calculated efficiency percentages
    pass_accuracy_pct: float = Field(default=0.0, ge=0, le=100)
    shot_accuracy_pct: float = Field(default=0.0, ge=0, le=100)
    tackle_success_pct: float = Field(default=0.0, ge=0, le=100)
    dribble_success_pct: float = Field(default=0.0, ge=0, le=100)
    aerial_duel_success_pct: float = Field(default=0.0, ge=0, le=100)

    # ============================================
    # METADATA
    # ============================================
    is_starter: bool = Field(default=False)
    substituted_in_minute: int | None = Field(default=None, ge=0, le=120)
    substituted_out_minute: int | None = Field(default=None, ge=0, le=120)

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
    player: Optional["Player"] = Relationship(back_populates="player_stats")

    __table_args__ = (
        Index("idx_player_stats_player_season", "player_id", "season"),
        Index("idx_player_stats_player_date", "player_id", "date"),
        Index("idx_player_stats_org_date", "organization_id", "date"),
    )

    def calculate_efficiency_metrics(self) -> None:
        """Calculate efficiency percentages based on raw stats."""
        if self.passes_attempted > 0:
            self.pass_accuracy_pct = round((self.passes_completed / self.passes_attempted) * 100, 2)

        if self.shots > 0:
            self.shot_accuracy_pct = round((self.shots_on_target / self.shots) * 100, 2)

        if self.tackles_attempted > 0:
            self.tackle_success_pct = round((self.tackles_success / self.tackles_attempted) * 100, 2)

        if self.dribbles_attempted > 0:
            self.dribble_success_pct = round((self.dribbles_success / self.dribbles_attempted) * 100, 2)

        total_aerial = self.aerial_duels_won + self.aerial_duels_lost
        if total_aerial > 0:
            self.aerial_duel_success_pct = round((self.aerial_duels_won / total_aerial) * 100, 2)

    class Config:
        use_enum_values = True

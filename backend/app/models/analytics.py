"""Analytics models for ML training and predictions."""

from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func, UniqueConstraint

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.organization import Organization


class Match(SQLModel, table=True):
    """Match model for tracking games."""

    __tablename__ = "matches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date = Field(nullable=False, index=True)
    opponent: Optional[str] = Field(default=None, max_length=100)
    competition: Optional[str] = Field(default=None, max_length=100)
    home: bool = Field(default=True, nullable=False)
    minutes: Optional[int] = Field(default=None)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    player_stats: list["PlayerMatchStat"] = Relationship(back_populates="match")


class TrainingSession(SQLModel, table=True):
    """Training session model."""

    __tablename__ = "training_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date = Field(nullable=False, index=True)
    session_type: Optional[str] = Field(default=None, max_length=50)
    duration_min: Optional[int] = Field(default=None)
    rpe: Optional[float] = Field(default=None)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    player_loads: list["PlayerTrainingLoad"] = Relationship(back_populates="session")


class PlayerMatchStat(SQLModel, table=True):
    """Player match statistics."""

    __tablename__ = "player_match_stats"
    __table_args__ = (UniqueConstraint("player_id", "match_id", name="uq_player_match"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", nullable=False, index=True)
    match_id: UUID = Field(foreign_key="matches.id", nullable=False, index=True)
    minutes: Optional[int] = Field(default=None)
    goals: int = Field(default=0)
    assists: int = Field(default=0)
    shots: int = Field(default=0)
    xg: float = Field(default=0.0)
    key_passes: int = Field(default=0)
    duels_won: int = Field(default=0)
    sprints: int = Field(default=0)
    pressures: int = Field(default=0)
    def_actions: int = Field(default=0)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", nullable=False)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    match: Optional["Match"] = Relationship(back_populates="player_stats")
    player: Optional["Player"] = Relationship(back_populates="ml_match_stats")


class PlayerTrainingLoad(SQLModel, table=True):
    """Player training load tracking."""

    __tablename__ = "player_training_load"
    __table_args__ = (UniqueConstraint("player_id", "session_id", name="uq_player_session"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", nullable=False, index=True)
    session_id: UUID = Field(foreign_key="training_sessions.id", nullable=False, index=True)
    load_acute: Optional[float] = Field(default=None)
    load_chronic: Optional[float] = Field(default=None)
    monotony: Optional[float] = Field(default=None)
    strain: Optional[float] = Field(default=None)
    injury_history_flag: bool = Field(default=False, nullable=False)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", nullable=False)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    session: Optional["TrainingSession"] = Relationship(back_populates="player_loads")
    player: Optional["Player"] = Relationship(back_populates="ml_training_loads")


class PlayerFeatureDaily(SQLModel, table=True):
    """Daily player features for ML."""

    __tablename__ = "player_features_daily"
    __table_args__ = (UniqueConstraint("player_id", "date", name="uq_player_date"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", nullable=False, index=True)
    date: date = Field(nullable=False, index=True)
    rolling_7d_load: Optional[float] = Field(default=None)
    rolling_21d_load: Optional[float] = Field(default=None)
    form_score: Optional[float] = Field(default=None)
    injury_flag: bool = Field(default=False, nullable=False)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", nullable=False)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationship
    player: Optional["Player"] = Relationship(back_populates="ml_features_daily")


class PlayerPrediction(SQLModel, table=True):
    """ML predictions for players."""

    __tablename__ = "player_predictions"
    __table_args__ = (UniqueConstraint("player_id", "date", "target", name="uq_player_date_target"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", nullable=False, index=True)
    date: date = Field(nullable=False, index=True)
    target: str = Field(nullable=False, max_length=50)  # 'injury_risk' | 'performance_index'
    model_name: str = Field(nullable=False, max_length=100)
    model_version: str = Field(nullable=False, max_length=50)
    y_pred: Optional[float] = Field(default=None)
    y_proba: Optional[float] = Field(default=None)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", nullable=False)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationship
    player: Optional["Player"] = Relationship(back_populates="ml_predictions")

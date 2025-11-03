"""Match and Attendance models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class MatchType(str, Enum):
    """Match types."""

    LEAGUE = "LEAGUE"
    CUP = "CUP"
    FRIENDLY = "FRIENDLY"
    TRAINING_MATCH = "TRAINING_MATCH"


class MatchResult(str, Enum):
    """Match result."""

    WIN = "WIN"
    DRAW = "DRAW"
    LOSS = "LOSS"
    NOT_PLAYED = "NOT_PLAYED"


class Match(SQLModel, table=True):
    """Match/Game model."""

    __tablename__ = "matches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    match_date: datetime
    match_type: MatchType = Field(default=MatchType.LEAGUE)

    # Teams
    team_id: UUID = Field(foreign_key="teams.id", index=True)
    opponent_name: str = Field(max_length=255)
    is_home: bool = Field(default=True)

    # Score
    goals_for: int | None = Field(default=None)
    goals_against: int | None = Field(default=None)
    result: MatchResult = Field(default=MatchResult.NOT_PLAYED)

    # Location
    venue: str | None = Field(default=None, max_length=255)
    weather: str | None = Field(default=None, max_length=100)
    temperature_c: float | None = Field(default=None)

    # Video link
    video_id: UUID | None = Field(default=None, foreign_key="videos.id", index=True)

    # Notes
    notes: str | None = Field(default=None, sa_column=Column(Text))

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True


class Attendance(SQLModel, table=True):
    """Player attendance/participation in match."""

    __tablename__ = "attendances"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    match_id: UUID = Field(foreign_key="matches.id", index=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Participation
    is_starter: bool = Field(default=False)
    minutes_played: int = Field(default=0)
    jersey_number: int | None = Field(default=None)

    # Events
    goals: int = Field(default=0)
    assists: int = Field(default=0)
    yellow_cards: int = Field(default=0)
    red_card: bool = Field(default=False)

    # Ratings
    coach_rating: float | None = Field(default=None)  # 0-10
    analyst_rating: float | None = Field(default=None)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

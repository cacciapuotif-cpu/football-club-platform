"""Match schemas for request/response."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.match import MatchResult, MatchType


# ============================================
# MATCH SCHEMAS
# ============================================


class MatchBase(BaseModel):
    """Base match schema."""

    match_date: datetime = Field(..., description="Match date and time")
    match_type: MatchType = Field(MatchType.LEAGUE, description="Type of match")
    team_id: UUID = Field(..., description="Team ID")
    opponent_name: str = Field(..., min_length=1, max_length=255, description="Opponent team name")
    is_home: bool = Field(True, description="Whether the match is at home")
    venue: Optional[str] = Field(None, max_length=255, description="Match venue/stadium")
    weather: Optional[str] = Field(None, max_length=100, description="Weather conditions")
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    notes: Optional[str] = Field(None, description="Additional notes")


class MatchCreate(MatchBase):
    """Schema for creating a match."""

    organization_id: UUID = Field(..., description="Organization ID")


class MatchUpdate(BaseModel):
    """Schema for updating a match."""

    match_date: Optional[datetime] = None
    match_type: Optional[MatchType] = None
    opponent_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_home: Optional[bool] = None
    goals_for: Optional[int] = Field(None, ge=0, description="Goals scored")
    goals_against: Optional[int] = Field(None, ge=0, description="Goals conceded")
    result: Optional[MatchResult] = None
    venue: Optional[str] = Field(None, max_length=255)
    weather: Optional[str] = Field(None, max_length=100)
    temperature_c: Optional[float] = None
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for match response."""

    id: UUID
    organization_id: UUID
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    result: MatchResult
    video_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Schema for match list response with pagination."""

    matches: list[MatchResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# ATTENDANCE SCHEMAS
# ============================================


class AttendanceBase(BaseModel):
    """Base attendance schema."""

    match_id: UUID = Field(..., description="Match ID")
    player_id: UUID = Field(..., description="Player ID")
    is_starter: bool = Field(False, description="Whether player started the match")
    minutes_played: int = Field(0, ge=0, le=120, description="Minutes played")
    jersey_number: Optional[int] = Field(None, ge=1, le=99, description="Jersey number worn")
    goals: int = Field(0, ge=0, description="Goals scored")
    assists: int = Field(0, ge=0, description="Assists")
    yellow_cards: int = Field(0, ge=0, le=2, description="Yellow cards received")
    red_card: bool = Field(False, description="Red card received")
    coach_rating: Optional[float] = Field(None, ge=0, le=10, description="Coach rating (0-10)")
    analyst_rating: Optional[float] = Field(None, ge=0, le=10, description="Analyst rating (0-10)")


class AttendanceCreate(AttendanceBase):
    """Schema for creating attendance."""

    organization_id: UUID = Field(..., description="Organization ID")


class AttendanceUpdate(BaseModel):
    """Schema for updating attendance."""

    is_starter: Optional[bool] = None
    minutes_played: Optional[int] = Field(None, ge=0, le=120)
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    goals: Optional[int] = Field(None, ge=0)
    assists: Optional[int] = Field(None, ge=0)
    yellow_cards: Optional[int] = Field(None, ge=0, le=2)
    red_card: Optional[bool] = None
    coach_rating: Optional[float] = Field(None, ge=0, le=10)
    analyst_rating: Optional[float] = Field(None, ge=0, le=10)


class AttendanceResponse(AttendanceBase):
    """Schema for attendance response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceWithPlayer(AttendanceResponse):
    """Schema for attendance with player details."""

    player_first_name: str
    player_last_name: str
    player_position: Optional[str] = None


# ============================================
# MATCH STATISTICS SCHEMAS
# ============================================


class MatchStatsResponse(BaseModel):
    """Schema for match statistics."""

    match_id: UUID
    match_date: datetime
    opponent_name: str
    is_home: bool
    result: MatchResult
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None

    # Attendance stats
    total_players: int = 0
    starters: int = 0
    substitutes: int = 0
    total_goals: int = 0
    total_assists: int = 0
    total_yellow_cards: int = 0
    total_red_cards: int = 0

    # Average ratings
    avg_coach_rating: Optional[float] = None
    avg_analyst_rating: Optional[float] = None


class TeamMatchStatsResponse(BaseModel):
    """Schema for team-wide match statistics."""

    team_id: UUID
    team_name: str

    # Overall stats
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    not_played: int = 0

    # Goals
    total_goals_for: int = 0
    total_goals_against: int = 0
    goal_difference: int = 0

    # Averages
    avg_goals_for: float = 0.0
    avg_goals_against: float = 0.0

    # Home/Away splits
    home_matches: int = 0
    away_matches: int = 0
    home_wins: int = 0
    away_wins: int = 0

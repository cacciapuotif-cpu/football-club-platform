"""Team schemas for request/response."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# TEAM SCHEMAS
# ============================================


class TeamBase(BaseModel):
    """Base team schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    category: Optional[str] = Field(None, max_length=100, description="Team category (e.g., U15, U17, Serie C)")
    season_id: Optional[UUID] = Field(None, description="Season ID")


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    organization_id: UUID = Field(..., description="Organization ID")


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    season_id: Optional[UUID] = None


class TeamResponse(TeamBase):
    """Schema for team response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamWithPlayers(TeamResponse):
    """Schema for team with players count."""

    players_count: int = Field(0, description="Number of players in the team")


class TeamListResponse(BaseModel):
    """Schema for team list response with pagination."""

    teams: list[TeamResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# SEASON SCHEMAS
# ============================================


class SeasonBase(BaseModel):
    """Base season schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Season name (e.g., 2024-2025)")
    start_date: date = Field(..., description="Season start date")
    end_date: date = Field(..., description="Season end date")
    is_active: bool = Field(True, description="Whether the season is active")


class SeasonCreate(SeasonBase):
    """Schema for creating a season."""

    organization_id: UUID = Field(..., description="Organization ID")


class SeasonUpdate(BaseModel):
    """Schema for updating a season."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class SeasonResponse(SeasonBase):
    """Schema for season response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class SeasonWithTeams(SeasonResponse):
    """Schema for season with teams count."""

    teams_count: int = Field(0, description="Number of teams in the season")


# ============================================
# TEAM STATISTICS SCHEMAS
# ============================================


class TeamStatsResponse(BaseModel):
    """Schema for team statistics."""

    team_id: UUID
    team_name: str
    players_count: int
    avg_age: Optional[float] = None
    total_training_sessions: int = 0
    total_matches: int = 0
    active_injuries: int = 0


class TeamPlayerResponse(BaseModel):
    """Simplified player schema for team endpoints."""

    id: UUID
    first_name: str
    last_name: str
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    status: str

    class Config:
        from_attributes = True

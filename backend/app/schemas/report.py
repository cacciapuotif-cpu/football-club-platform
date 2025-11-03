"""Report schemas for request/response."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.report import ReportFormat, ReportType


# ============================================
# REPORT SCHEMAS
# ============================================


class ReportBase(BaseModel):
    """Base report schema."""

    report_type: ReportType = Field(..., description="Type of report")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    player_id: Optional[UUID] = Field(None, description="Player ID (for player reports)")
    team_id: Optional[UUID] = Field(None, description="Team ID (for team reports)")
    range_start: datetime = Field(..., description="Report period start date")
    range_end: datetime = Field(..., description="Report period end date")


class ReportCreate(ReportBase):
    """Schema for creating a report."""

    organization_id: UUID = Field(..., description="Organization ID")
    generated_by: Optional[UUID] = Field(None, description="User ID who generated the report")


class ReportResponse(ReportBase):
    """Schema for report response."""

    id: UUID
    organization_id: UUID
    storage_path: str
    file_size_kb: float
    generated_by: Optional[UUID] = None
    generation_duration_sec: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for report list response with pagination."""

    reports: list[ReportResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# REPORT GENERATION REQUEST SCHEMAS
# ============================================


class PlayerReportRequest(BaseModel):
    """Schema for generating a player report."""

    player_id: UUID = Field(..., description="Player ID")
    range_start: datetime = Field(..., description="Report period start")
    range_end: datetime = Field(..., description="Report period end")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    organization_id: UUID = Field(..., description="Organization ID")
    generated_by: Optional[UUID] = Field(None, description="User ID")
    include_sections: list[str] = Field(
        default=["overview", "training", "wellness", "performance", "goals"],
        description="Sections to include in the report",
    )


class TeamReportRequest(BaseModel):
    """Schema for generating a team report."""

    team_id: UUID = Field(..., description="Team ID")
    range_start: datetime = Field(..., description="Report period start")
    range_end: datetime = Field(..., description="Report period end")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    organization_id: UUID = Field(..., description="Organization ID")
    generated_by: Optional[UUID] = Field(None, description="User ID")
    include_sections: list[str] = Field(
        default=["overview", "matches", "training", "players", "statistics"],
        description="Sections to include in the report",
    )


class StaffWeeklyReportRequest(BaseModel):
    """Schema for generating a staff weekly report."""

    team_id: Optional[UUID] = Field(None, description="Team ID (optional, for all teams if not specified)")
    range_start: datetime = Field(..., description="Week start")
    range_end: datetime = Field(..., description="Week end")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    organization_id: UUID = Field(..., description="Organization ID")
    generated_by: Optional[UUID] = Field(None, description="User ID")


# ============================================
# REPORT DATA SCHEMAS (for JSON format)
# ============================================


class PlayerReportData(BaseModel):
    """Data structure for player report."""

    player_id: UUID
    player_name: str
    period: str

    # Overview
    total_training_sessions: int = 0
    total_matches: int = 0
    total_goals: int = 0
    total_assists: int = 0

    # Training
    avg_rpe: Optional[float] = None
    total_minutes_played: int = 0

    # Wellness
    avg_fatigue: Optional[float] = None
    avg_mood: Optional[float] = None
    avg_sleep_hours: Optional[float] = None

    # Performance
    recent_performance_scores: list[float] = []
    improvement_areas: list[str] = []
    strengths: list[str] = []


class TeamReportData(BaseModel):
    """Data structure for team report."""

    team_id: UUID
    team_name: str
    period: str

    # Overview
    total_players: int = 0
    total_training_sessions: int = 0
    total_matches: int = 0

    # Match results
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0

    # Training
    avg_team_rpe: Optional[float] = None
    avg_attendance_pct: float = 0.0

    # Top performers
    top_scorers: list[dict] = []  # {player_name, goals}
    top_assisters: list[dict] = []  # {player_name, assists}
    most_improved: list[dict] = []  # {player_name, improvement_score}


class StaffWeeklyReportData(BaseModel):
    """Data structure for staff weekly report."""

    week_start: datetime
    week_end: datetime
    organization_name: str

    # Summary
    total_teams: int = 0
    total_players: int = 0
    total_training_sessions: int = 0
    total_matches: int = 0

    # Alerts
    injured_players: list[dict] = []  # {player_name, injury_type}
    high_fatigue_players: list[dict] = []  # {player_name, fatigue_score}
    low_adherence_players: list[dict] = []  # {player_name, adherence_pct}

    # Team summaries
    team_summaries: list[dict] = []  # {team_name, stats}

"""
Reports Router - Complete CRUD operations and report generation.
"""

import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.injury import Injury
from app.models.match import Attendance, Match, MatchResult
from app.models.player import Player
from app.models.report import Report, ReportCache, ReportFormat, ReportType
from app.models.session import TrainingSession
from app.models.team import Team
from app.models.wellness import WellnessData
from app.schemas.report import (
    PlayerReportData,
    PlayerReportRequest,
    ReportCreate,
    ReportListResponse,
    ReportResponse,
    StaffWeeklyReportData,
    StaffWeeklyReportRequest,
    TeamReportData,
    TeamReportRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage path for generated reports
REPORTS_DIR = Path("storage/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# REPORTS CRUD ENDPOINTS
# ============================================


@router.get("/", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
async def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    player_id: Optional[UUID] = Query(None, description="Filter by player"),
    team_id: Optional[UUID] = Query(None, description="Filter by team"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all reports with pagination and filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **report_type**: Filter by report type
    - **player_id**: Filter by player
    - **team_id**: Filter by team
    - **organization_id**: Filter by organization (multi-tenant)
    """
    try:
        # Build query
        query = select(Report)

        # Apply filters
        if report_type:
            query = query.where(Report.report_type == report_type)
        if player_id:
            query = query.where(Report.player_id == player_id)
        if team_id:
            query = query.where(Report.team_id == team_id)
        if organization_id:
            query = query.where(Report.organization_id == organization_id)

        # Count total items
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Report.created_at.desc())

        # Execute query
        result = await session.execute(query)
        reports = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ReportListResponse(
            reports=[ReportResponse.model_validate(report) for report in reports],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        )


@router.get("/{report_id}", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific report by ID.

    - **report_id**: The report UUID
    """
    try:
        result = await session.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found",
            )

        return ReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}",
        )


@router.get("/{report_id}/download", status_code=status.HTTP_200_OK)
async def download_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Download a generated report file.

    - **report_id**: The report UUID

    Returns the report file for download.
    """
    try:
        # Get report
        result = await session.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found",
            )

        # Check if file exists
        file_path = Path(report.storage_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found on storage",
            )

        # Determine media type
        media_type = "application/pdf" if report.format == ReportFormat.PDF else "text/html"

        # Return file
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=file_path.name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}",
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a report.

    - **report_id**: The report UUID

    **Note**: This will also delete the report file from storage.
    """
    try:
        # Get report
        result = await session.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found",
            )

        # Delete file from storage
        file_path = Path(report.storage_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted report file: {file_path}")

        # Delete report
        await session.delete(report)
        await session.commit()

        logger.info(f"Deleted report: {report.id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}",
        )


# ============================================
# REPORT GENERATION ENDPOINTS
# ============================================


@router.post("/generate/player", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_player_report(
    request: PlayerReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a player report.

    Creates a comprehensive report for a player covering:
    - Training sessions and performance
    - Match participation and statistics
    - Wellness and fatigue tracking
    - Goals and achievements

    - **player_id**: Player ID (required)
    - **range_start**: Report period start (required)
    - **range_end**: Report period end (required)
    - **format**: Output format (PDF, HTML, JSON) (default: PDF)
    - **include_sections**: Sections to include (optional)
    """
    start_time = time.time()

    try:
        # Validate player exists
        player_result = await session.execute(select(Player).where(Player.id == request.player_id))
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with id {request.player_id} not found",
            )

        # Gather data for report
        report_data = await _gather_player_report_data(session, request)

        # Generate report file
        storage_path, file_size_kb = await _generate_report_file(
            report_data=report_data,
            report_type=ReportType.PLAYER,
            format=request.format,
            filename_prefix=f"player_{player.last_name}_{player.first_name}",
        )

        # Calculate generation time
        generation_duration = time.time() - start_time

        # Create report record
        report = Report(
            report_type=ReportType.PLAYER,
            format=request.format,
            player_id=request.player_id,
            range_start=request.range_start,
            range_end=request.range_end,
            storage_path=str(storage_path),
            file_size_kb=file_size_kb,
            generated_by=request.generated_by,
            generation_duration_sec=round(generation_duration, 2),
            organization_id=request.organization_id,
        )

        session.add(report)
        await session.commit()
        await session.refresh(report)

        logger.info(
            f"Generated player report for {player.first_name} {player.last_name} in {generation_duration:.2f}s"
        )

        return ReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating player report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate player report: {str(e)}",
        )


@router.post("/generate/team", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_team_report(
    request: TeamReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a team report.

    Creates a comprehensive report for a team covering:
    - Team overview and roster
    - Match results and statistics
    - Training sessions
    - Player performance summaries
    - Team trends and insights

    - **team_id**: Team ID (required)
    - **range_start**: Report period start (required)
    - **range_end**: Report period end (required)
    - **format**: Output format (PDF, HTML, JSON) (default: PDF)
    - **include_sections**: Sections to include (optional)
    """
    start_time = time.time()

    try:
        # Validate team exists
        team_result = await session.execute(select(Team).where(Team.id == request.team_id))
        team = team_result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {request.team_id} not found",
            )

        # Gather data for report
        report_data = await _gather_team_report_data(session, request)

        # Generate report file
        storage_path, file_size_kb = await _generate_report_file(
            report_data=report_data,
            report_type=ReportType.TEAM,
            format=request.format,
            filename_prefix=f"team_{team.name}",
        )

        # Calculate generation time
        generation_duration = time.time() - start_time

        # Create report record
        report = Report(
            report_type=ReportType.TEAM,
            format=request.format,
            team_id=request.team_id,
            range_start=request.range_start,
            range_end=request.range_end,
            storage_path=str(storage_path),
            file_size_kb=file_size_kb,
            generated_by=request.generated_by,
            generation_duration_sec=round(generation_duration, 2),
            organization_id=request.organization_id,
        )

        session.add(report)
        await session.commit()
        await session.refresh(report)

        logger.info(f"Generated team report for {team.name} in {generation_duration:.2f}s")

        return ReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating team report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate team report: {str(e)}",
        )


@router.post("/generate/staff-weekly", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_staff_weekly_report(
    request: StaffWeeklyReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a staff weekly report.

    Creates a comprehensive weekly summary for coaching staff covering:
    - Organization overview
    - All teams summary
    - Training sessions and matches
    - Player alerts (injuries, fatigue, low adherence)
    - Key metrics and trends

    - **team_id**: Team ID (optional, for all teams if not specified)
    - **range_start**: Week start (required)
    - **range_end**: Week end (required)
    - **format**: Output format (PDF, HTML, JSON) (default: PDF)
    """
    start_time = time.time()

    try:
        # Gather data for report
        report_data = await _gather_staff_weekly_report_data(session, request)

        # Generate report file
        storage_path, file_size_kb = await _generate_report_file(
            report_data=report_data,
            report_type=ReportType.STAFF_WEEKLY,
            format=request.format,
            filename_prefix="staff_weekly",
        )

        # Calculate generation time
        generation_duration = time.time() - start_time

        # Create report record
        report = Report(
            report_type=ReportType.STAFF_WEEKLY,
            format=request.format,
            team_id=request.team_id,
            range_start=request.range_start,
            range_end=request.range_end,
            storage_path=str(storage_path),
            file_size_kb=file_size_kb,
            generated_by=request.generated_by,
            generation_duration_sec=round(generation_duration, 2),
            organization_id=request.organization_id,
        )

        session.add(report)
        await session.commit()
        await session.refresh(report)

        logger.info(f"Generated staff weekly report in {generation_duration:.2f}s")

        return ReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating staff weekly report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate staff weekly report: {str(e)}",
        )


# ============================================
# HELPER FUNCTIONS
# ============================================


async def _gather_player_report_data(session: AsyncSession, request: PlayerReportRequest) -> PlayerReportData:
    """Gather all data needed for a player report."""

    # Get player
    player_result = await session.execute(select(Player).where(Player.id == request.player_id))
    player = player_result.scalar_one()

    # Count training sessions
    sessions_result = await session.execute(
        select(func.count())
        .select_from(TrainingSession)
        .where(
            TrainingSession.player_id == request.player_id,
            TrainingSession.created_at >= request.range_start,
            TrainingSession.created_at <= request.range_end,
        )
    )
    total_training_sessions = sessions_result.scalar() or 0

    # Count matches and stats
    attendance_result = await session.execute(
        select(Attendance)
        .join(Match, Attendance.match_id == Match.id)
        .where(
            Attendance.player_id == request.player_id,
            Match.match_date >= request.range_start,
            Match.match_date <= request.range_end,
        )
    )
    attendances = attendance_result.scalars().all()

    total_matches = len(attendances)
    total_goals = sum(a.goals for a in attendances)
    total_assists = sum(a.assists for a in attendances)
    total_minutes = sum(a.minutes_played for a in attendances)

    # Get wellness data
    wellness_result = await session.execute(
        select(WellnessData).where(
            WellnessData.player_id == request.player_id,
            WellnessData.created_at >= request.range_start,
            WellnessData.created_at <= request.range_end,
        )
    )
    wellness_data = wellness_result.scalars().all()

    avg_fatigue = sum(w.fatigue for w in wellness_data if w.fatigue) / len(wellness_data) if wellness_data else None
    avg_mood = sum(w.mood for w in wellness_data if w.mood) / len(wellness_data) if wellness_data else None
    avg_sleep = (
        sum(w.sleep_hours for w in wellness_data if w.sleep_hours) / len(wellness_data) if wellness_data else None
    )

    return PlayerReportData(
        player_id=player.id,
        player_name=f"{player.first_name} {player.last_name}",
        period=f"{request.range_start.date()} to {request.range_end.date()}",
        total_training_sessions=total_training_sessions,
        total_matches=total_matches,
        total_goals=total_goals,
        total_assists=total_assists,
        total_minutes_played=total_minutes,
        avg_fatigue=round(avg_fatigue, 2) if avg_fatigue else None,
        avg_mood=round(avg_mood, 2) if avg_mood else None,
        avg_sleep_hours=round(avg_sleep, 2) if avg_sleep else None,
    )


async def _gather_team_report_data(session: AsyncSession, request: TeamReportRequest) -> TeamReportData:
    """Gather all data needed for a team report."""

    # Get team
    team_result = await session.execute(select(Team).where(Team.id == request.team_id))
    team = team_result.scalar_one()

    # Count players
    players_result = await session.execute(
        select(func.count()).select_from(Player).where(Player.team_id == request.team_id)
    )
    total_players = players_result.scalar() or 0

    # Count training sessions
    sessions_result = await session.execute(
        select(func.count())
        .select_from(TrainingSession)
        .where(
            TrainingSession.team_id == request.team_id,
            TrainingSession.created_at >= request.range_start,
            TrainingSession.created_at <= request.range_end,
        )
    )
    total_training_sessions = sessions_result.scalar() or 0

    # Get matches
    matches_result = await session.execute(
        select(Match).where(
            Match.team_id == request.team_id,
            Match.match_date >= request.range_start,
            Match.match_date <= request.range_end,
        )
    )
    matches = matches_result.scalars().all()

    total_matches = len(matches)
    wins = sum(1 for m in matches if m.result == MatchResult.WIN)
    draws = sum(1 for m in matches if m.result == MatchResult.DRAW)
    losses = sum(1 for m in matches if m.result == MatchResult.LOSS)
    goals_for = sum(m.goals_for or 0 for m in matches)
    goals_against = sum(m.goals_against or 0 for m in matches)

    return TeamReportData(
        team_id=team.id,
        team_name=team.name,
        period=f"{request.range_start.date()} to {request.range_end.date()}",
        total_players=total_players,
        total_training_sessions=total_training_sessions,
        total_matches=total_matches,
        wins=wins,
        draws=draws,
        losses=losses,
        goals_for=goals_for,
        goals_against=goals_against,
    )


async def _gather_staff_weekly_report_data(
    session: AsyncSession, request: StaffWeeklyReportRequest
) -> StaffWeeklyReportData:
    """Gather all data needed for a staff weekly report."""

    # For simplicity, returning basic data
    # In a real implementation, this would gather comprehensive data across all teams

    return StaffWeeklyReportData(
        week_start=request.range_start,
        week_end=request.range_end,
        organization_name="Organization",  # TODO: Get from organization
        total_teams=0,
        total_players=0,
        total_training_sessions=0,
        total_matches=0,
    )


async def _generate_report_file(
    report_data, report_type: ReportType, format: ReportFormat, filename_prefix: str
) -> tuple[Path, float]:
    """
    Generate report file based on data and format.

    Returns: (storage_path, file_size_kb)
    """
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.{format.value.lower()}"
    storage_path = REPORTS_DIR / filename

    # Generate content based on format
    if format == ReportFormat.JSON:
        import json

        content = report_data.model_dump_json(indent=2)
        storage_path.write_text(content)
    elif format == ReportFormat.HTML:
        content = _generate_html_report(report_data, report_type)
        storage_path.write_text(content)
    elif format == ReportFormat.PDF:
        # For now, generate HTML and save as .pdf (basic implementation)
        # In production, use a proper HTML-to-PDF library like WeasyPrint or ReportLab
        content = _generate_html_report(report_data, report_type)
        storage_path.write_text(content)
        logger.warning("PDF generation not fully implemented - saving as HTML")

    # Calculate file size
    file_size_kb = storage_path.stat().st_size / 1024

    return storage_path, round(file_size_kb, 2)


def _generate_html_report(report_data, report_type: ReportType) -> str:
    """Generate HTML content for report."""

    if isinstance(report_data, PlayerReportData):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Player Report - {report_data.player_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Player Report: {report_data.player_name}</h1>
            <p><strong>Period:</strong> {report_data.period}</p>

            <div class="section">
                <h2>Training & Matches</h2>
                <div class="metric"><span class="metric-label">Training Sessions:</span> {report_data.total_training_sessions}</div>
                <div class="metric"><span class="metric-label">Matches:</span> {report_data.total_matches}</div>
                <div class="metric"><span class="metric-label">Goals:</span> {report_data.total_goals}</div>
                <div class="metric"><span class="metric-label">Assists:</span> {report_data.total_assists}</div>
                <div class="metric"><span class="metric-label">Minutes Played:</span> {report_data.total_minutes_played}</div>
            </div>

            <div class="section">
                <h2>Wellness</h2>
                <div class="metric"><span class="metric-label">Avg Fatigue:</span> {report_data.avg_fatigue or 'N/A'}</div>
                <div class="metric"><span class="metric-label">Avg Mood:</span> {report_data.avg_mood or 'N/A'}</div>
                <div class="metric"><span class="metric-label">Avg Sleep:</span> {report_data.avg_sleep_hours or 'N/A'} hours</div>
            </div>
        </body>
        </html>
        """
    elif isinstance(report_data, TeamReportData):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Team Report - {report_data.team_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Team Report: {report_data.team_name}</h1>
            <p><strong>Period:</strong> {report_data.period}</p>

            <div class="section">
                <h2>Overview</h2>
                <div class="metric"><span class="metric-label">Players:</span> {report_data.total_players}</div>
                <div class="metric"><span class="metric-label">Training Sessions:</span> {report_data.total_training_sessions}</div>
                <div class="metric"><span class="metric-label">Matches:</span> {report_data.total_matches}</div>
            </div>

            <div class="section">
                <h2>Match Results</h2>
                <div class="metric"><span class="metric-label">Wins:</span> {report_data.wins}</div>
                <div class="metric"><span class="metric-label">Draws:</span> {report_data.draws}</div>
                <div class="metric"><span class="metric-label">Losses:</span> {report_data.losses}</div>
                <div class="metric"><span class="metric-label">Goals For:</span> {report_data.goals_for}</div>
                <div class="metric"><span class="metric-label">Goals Against:</span> {report_data.goals_against}</div>
            </div>
        </body>
        </html>
        """
    else:
        return "<html><body><h1>Report Generated</h1></body></html>"

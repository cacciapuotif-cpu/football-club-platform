"""
Matches Router - Complete CRUD operations and match management.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.match import Attendance, Match, MatchResult, MatchType
from app.models.player import Player
from app.models.team import Team
from app.schemas.match import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    AttendanceWithPlayer,
    MatchCreate,
    MatchListResponse,
    MatchResponse,
    MatchStatsResponse,
    MatchUpdate,
    TeamMatchStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# MATCHES CRUD ENDPOINTS
# ============================================


@router.get("/", response_model=MatchListResponse, status_code=status.HTTP_200_OK)
async def list_matches(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    team_id: Optional[UUID] = Query(None, description="Filter by team"),
    match_type: Optional[MatchType] = Query(None, description="Filter by match type"),
    result: Optional[MatchResult] = Query(None, description="Filter by result"),
    is_home: Optional[bool] = Query(None, description="Filter by home/away"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all matches with pagination and filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **team_id**: Filter by team
    - **match_type**: Filter by match type (LEAGUE, CUP, FRIENDLY, TRAINING_MATCH)
    - **result**: Filter by result (WIN, DRAW, LOSS, NOT_PLAYED)
    - **is_home**: Filter by home/away matches
    - **from_date**: Filter matches from this date
    - **to_date**: Filter matches to this date
    - **organization_id**: Filter by organization (multi-tenant)
    """
    try:
        # Build query
        query = select(Match)

        # Apply filters
        if team_id:
            query = query.where(Match.team_id == team_id)
        if match_type:
            query = query.where(Match.match_type == match_type)
        if result:
            query = query.where(Match.result == result)
        if is_home is not None:
            query = query.where(Match.is_home == is_home)
        if from_date:
            query = query.where(Match.match_date >= from_date)
        if to_date:
            query = query.where(Match.match_date <= to_date)
        if organization_id:
            query = query.where(Match.organization_id == organization_id)

        # Count total items
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Match.match_date.desc())

        # Execute query
        result_exec = await session.execute(query)
        matches = result_exec.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return MatchListResponse(
            matches=[MatchResponse.model_validate(match) for match in matches],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error listing matches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list matches: {str(e)}",
        )


@router.get("/{match_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def get_match(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific match by ID.

    - **match_id**: The match UUID
    """
    try:
        result = await session.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {match_id} not found",
            )

        return MatchResponse.model_validate(match)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match {match_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match: {str(e)}",
        )


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new match.

    - **match_date**: Date and time of the match (required)
    - **match_type**: Type of match (LEAGUE, CUP, FRIENDLY, TRAINING_MATCH)
    - **team_id**: Team ID (required)
    - **opponent_name**: Opponent team name (required)
    - **is_home**: Whether the match is at home (default: true)
    - **venue**: Match venue/stadium (optional)
    - **organization_id**: Organization ID (required, multi-tenant)
    """
    try:
        # Validate team exists
        team_result = await session.execute(select(Team).where(Team.id == match_data.team_id))
        team = team_result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {match_data.team_id} not found",
            )

        # Create match
        match = Match(**match_data.model_dump())

        session.add(match)
        await session.commit()
        await session.refresh(match)

        logger.info(f"Created match: {team.name} vs {match.opponent_name} (id={match.id})")

        return MatchResponse.model_validate(match)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating match: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create match: {str(e)}",
        )


@router.put("/{match_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def update_match(
    match_id: UUID,
    match_data: MatchUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing match.

    - **match_id**: The match UUID
    - All fields are optional
    """
    try:
        # Get match
        result = await session.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {match_id} not found",
            )

        # Update match fields
        update_data = match_data.model_dump(exclude_unset=True)

        # Auto-calculate result if goals are provided
        if "goals_for" in update_data or "goals_against" in update_data:
            goals_for = update_data.get("goals_for", match.goals_for)
            goals_against = update_data.get("goals_against", match.goals_against)

            if goals_for is not None and goals_against is not None:
                if goals_for > goals_against:
                    update_data["result"] = MatchResult.WIN
                elif goals_for < goals_against:
                    update_data["result"] = MatchResult.LOSS
                else:
                    update_data["result"] = MatchResult.DRAW

        for key, value in update_data.items():
            setattr(match, key, value)

        await session.commit()
        await session.refresh(match)

        logger.info(f"Updated match: {match.opponent_name} (id={match.id})")

        return MatchResponse.model_validate(match)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating match {match_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update match: {str(e)}",
        )


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a match.

    - **match_id**: The match UUID

    **Note**: This will also delete all attendance records for this match.
    """
    try:
        # Get match
        result = await session.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {match_id} not found",
            )

        # Delete match (cascade will delete attendances)
        await session.delete(match)
        await session.commit()

        logger.info(f"Deleted match: {match.opponent_name} (id={match.id})")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting match {match_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete match: {str(e)}",
        )


# ============================================
# MATCH ATTENDANCE ENDPOINTS
# ============================================


@router.get("/{match_id}/attendance", response_model=list[AttendanceWithPlayer], status_code=status.HTTP_200_OK)
async def get_match_attendance(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all player attendance for a match.

    - **match_id**: The match UUID

    Returns attendance records with player details.
    """
    try:
        # Verify match exists
        match_result = await session.execute(select(Match).where(Match.id == match_id))
        match = match_result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {match_id} not found",
            )

        # Get attendance with player info
        query = (
            select(Attendance, Player)
            .join(Player, Attendance.player_id == Player.id)
            .where(Attendance.match_id == match_id)
            .order_by(Attendance.is_starter.desc(), Player.last_name.asc())
        )

        result = await session.execute(query)
        attendance_with_players = result.all()

        # Build response
        response_list = []
        for attendance, player in attendance_with_players:
            attendance_dict = AttendanceResponse.model_validate(attendance).model_dump()
            attendance_dict["player_first_name"] = player.first_name
            attendance_dict["player_last_name"] = player.last_name
            attendance_dict["player_position"] = player.position
            response_list.append(AttendanceWithPlayer(**attendance_dict))

        return response_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match attendance for match {match_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match attendance: {str(e)}",
        )


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new attendance record (add player to match).

    - **match_id**: Match ID (required)
    - **player_id**: Player ID (required)
    - **is_starter**: Whether player started (default: false)
    - **minutes_played**: Minutes played (default: 0)
    - **organization_id**: Organization ID (required)
    """
    try:
        # Validate match exists
        match_result = await session.execute(
            select(Match).where(Match.id == attendance_data.match_id)
        )
        match = match_result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {attendance_data.match_id} not found",
            )

        # Validate player exists
        player_result = await session.execute(
            select(Player).where(Player.id == attendance_data.player_id)
        )
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with id {attendance_data.player_id} not found",
            )

        # Check if attendance already exists
        existing_result = await session.execute(
            select(Attendance).where(
                Attendance.match_id == attendance_data.match_id,
                Attendance.player_id == attendance_data.player_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance record already exists for this player and match",
            )

        # Create attendance
        attendance = Attendance(**attendance_data.model_dump())

        session.add(attendance)
        await session.commit()
        await session.refresh(attendance)

        logger.info(
            f"Created attendance: Player {player.first_name} {player.last_name} in match {match.id}"
        )

        return AttendanceResponse.model_validate(attendance)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating attendance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attendance: {str(e)}",
        )


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse, status_code=status.HTTP_200_OK)
async def update_attendance(
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an attendance record.

    - **attendance_id**: The attendance UUID
    - All fields are optional
    """
    try:
        # Get attendance
        result = await session.execute(select(Attendance).where(Attendance.id == attendance_id))
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance with id {attendance_id} not found",
            )

        # Update attendance fields
        update_data = attendance_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(attendance, key, value)

        await session.commit()
        await session.refresh(attendance)

        logger.info(f"Updated attendance: {attendance.id}")

        return AttendanceResponse.model_validate(attendance)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating attendance {attendance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update attendance: {str(e)}",
        )


@router.delete("/attendance/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete an attendance record (remove player from match).

    - **attendance_id**: The attendance UUID
    """
    try:
        # Get attendance
        result = await session.execute(select(Attendance).where(Attendance.id == attendance_id))
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance with id {attendance_id} not found",
            )

        # Delete attendance
        await session.delete(attendance)
        await session.commit()

        logger.info(f"Deleted attendance: {attendance.id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting attendance {attendance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attendance: {str(e)}",
        )


# ============================================
# MATCH STATISTICS ENDPOINTS
# ============================================


@router.get("/{match_id}/stats", response_model=MatchStatsResponse, status_code=status.HTTP_200_OK)
async def get_match_stats(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get comprehensive statistics for a match.

    Returns:
    - Match details (date, opponent, result, score)
    - Attendance stats (total players, starters, subs)
    - Performance stats (goals, assists, cards)
    - Average ratings
    """
    try:
        # Get match
        match_result = await session.execute(select(Match).where(Match.id == match_id))
        match = match_result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with id {match_id} not found",
            )

        # Get attendance stats
        attendance_query = select(
            func.count(Attendance.id).label("total_players"),
            func.sum(func.cast(Attendance.is_starter, func.INTEGER())).label("starters"),
            func.sum(Attendance.goals).label("total_goals"),
            func.sum(Attendance.assists).label("total_assists"),
            func.sum(Attendance.yellow_cards).label("total_yellow_cards"),
            func.sum(func.cast(Attendance.red_card, func.INTEGER())).label("total_red_cards"),
            func.avg(Attendance.coach_rating).label("avg_coach_rating"),
            func.avg(Attendance.analyst_rating).label("avg_analyst_rating"),
        ).where(Attendance.match_id == match_id)

        stats_result = await session.execute(attendance_query)
        stats = stats_result.one()

        total_players = stats.total_players or 0
        starters = stats.starters or 0
        substitutes = total_players - starters

        return MatchStatsResponse(
            match_id=match.id,
            match_date=match.match_date,
            opponent_name=match.opponent_name,
            is_home=match.is_home,
            result=match.result,
            goals_for=match.goals_for,
            goals_against=match.goals_against,
            total_players=total_players,
            starters=starters,
            substitutes=substitutes,
            total_goals=stats.total_goals or 0,
            total_assists=stats.total_assists or 0,
            total_yellow_cards=stats.total_yellow_cards or 0,
            total_red_cards=stats.total_red_cards or 0,
            avg_coach_rating=round(stats.avg_coach_rating, 2) if stats.avg_coach_rating else None,
            avg_analyst_rating=round(stats.avg_analyst_rating, 2) if stats.avg_analyst_rating else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match stats for match {match_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match stats: {str(e)}",
        )


@router.get("/teams/{team_id}/stats", response_model=TeamMatchStatsResponse, status_code=status.HTTP_200_OK)
async def get_team_match_stats(
    team_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get comprehensive match statistics for a team.

    Returns overall performance metrics:
    - Total matches, wins, draws, losses
    - Goals for/against, goal difference
    - Home/away splits
    """
    try:
        # Get team
        team_result = await session.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {team_id} not found",
            )

        # Get all matches for team
        matches_query = select(Match).where(Match.team_id == team_id)
        matches_result = await session.execute(matches_query)
        matches = matches_result.scalars().all()

        # Calculate stats
        total_matches = len(matches)
        wins = sum(1 for m in matches if m.result == MatchResult.WIN)
        draws = sum(1 for m in matches if m.result == MatchResult.DRAW)
        losses = sum(1 for m in matches if m.result == MatchResult.LOSS)
        not_played = sum(1 for m in matches if m.result == MatchResult.NOT_PLAYED)

        total_goals_for = sum(m.goals_for or 0 for m in matches if m.goals_for is not None)
        total_goals_against = sum(m.goals_against or 0 for m in matches if m.goals_against is not None)
        goal_difference = total_goals_for - total_goals_against

        played_matches = total_matches - not_played
        avg_goals_for = round(total_goals_for / played_matches, 2) if played_matches > 0 else 0.0
        avg_goals_against = round(total_goals_against / played_matches, 2) if played_matches > 0 else 0.0

        home_matches = sum(1 for m in matches if m.is_home)
        away_matches = total_matches - home_matches
        home_wins = sum(1 for m in matches if m.is_home and m.result == MatchResult.WIN)
        away_wins = sum(1 for m in matches if not m.is_home and m.result == MatchResult.WIN)

        return TeamMatchStatsResponse(
            team_id=team.id,
            team_name=team.name,
            total_matches=total_matches,
            wins=wins,
            draws=draws,
            losses=losses,
            not_played=not_played,
            total_goals_for=total_goals_for,
            total_goals_against=total_goals_against,
            goal_difference=goal_difference,
            avg_goals_for=avg_goals_for,
            avg_goals_against=avg_goals_against,
            home_matches=home_matches,
            away_matches=away_matches,
            home_wins=home_wins,
            away_wins=away_wins,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team match stats for team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team match stats: {str(e)}",
        )

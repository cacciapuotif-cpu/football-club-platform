"""
Teams Router - Complete CRUD operations and team management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.injury import Injury
from app.models.match import Match
from app.models.player import Player
from app.models.session import TrainingSession
from app.models.team import Season, Team
from app.schemas.team import (
    SeasonCreate,
    SeasonResponse,
    SeasonUpdate,
    SeasonWithTeams,
    TeamCreate,
    TeamListResponse,
    TeamPlayerResponse,
    TeamResponse,
    TeamStatsResponse,
    TeamUpdate,
    TeamWithPlayers,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# TEAMS CRUD ENDPOINTS
# ============================================


@router.get("/", response_model=TeamListResponse, status_code=status.HTTP_200_OK)
async def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    season_id: Optional[UUID] = Query(None, description="Filter by season"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all teams with pagination and filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **category**: Filter by team category (e.g., U15, U17)
    - **season_id**: Filter by season
    - **organization_id**: Filter by organization (multi-tenant support)
    """
    try:
        # Build query
        query = select(Team)

        # Apply filters
        if category:
            query = query.where(Team.category == category)
        if season_id:
            query = query.where(Team.season_id == season_id)
        if organization_id:
            query = query.where(Team.organization_id == organization_id)

        # Count total items
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Team.created_at.desc())

        # Execute query
        result = await session.execute(query)
        teams = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return TeamListResponse(
            teams=[TeamResponse.model_validate(team) for team in teams],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error listing teams: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list teams: {str(e)}",
        )


@router.get("/{team_id}", response_model=TeamWithPlayers, status_code=status.HTTP_200_OK)
async def get_team(
    team_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific team by ID with player count.

    - **team_id**: The team UUID
    """
    try:
        # Get team
        result = await session.execute(
            select(Team).where(Team.id == team_id).options(selectinload(Team.players))
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {team_id} not found",
            )

        # Count players
        players_count = len(team.players) if team.players else 0

        # Return team with players count
        team_dict = TeamResponse.model_validate(team).model_dump()
        team_dict["players_count"] = players_count

        return TeamWithPlayers(**team_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team: {str(e)}",
        )


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new team.

    - **name**: Team name (required)
    - **category**: Team category (optional, e.g., U15, U17, Serie C)
    - **season_id**: Season ID (optional)
    - **organization_id**: Organization ID (required, multi-tenant)
    """
    try:
        # Validate season exists if provided
        if team_data.season_id:
            season_result = await session.execute(
                select(Season).where(Season.id == team_data.season_id)
            )
            season = season_result.scalar_one_or_none()
            if not season:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Season with id {team_data.season_id} not found",
                )

        # Create team
        team = Team(**team_data.model_dump())

        session.add(team)
        await session.commit()
        await session.refresh(team)

        logger.info(f"Created team: {team.name} (id={team.id})")

        return TeamResponse.model_validate(team)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating team: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}",
        )


@router.put("/{team_id}", response_model=TeamResponse, status_code=status.HTTP_200_OK)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing team.

    - **team_id**: The team UUID
    - **name**: New team name (optional)
    - **category**: New team category (optional)
    - **season_id**: New season ID (optional)
    """
    try:
        # Get team
        result = await session.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {team_id} not found",
            )

        # Validate season if provided
        if team_data.season_id:
            season_result = await session.execute(
                select(Season).where(Season.id == team_data.season_id)
            )
            season = season_result.scalar_one_or_none()
            if not season:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Season with id {team_data.season_id} not found",
                )

        # Update team fields
        update_data = team_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(team, key, value)

        await session.commit()
        await session.refresh(team)

        logger.info(f"Updated team: {team.name} (id={team.id})")

        return TeamResponse.model_validate(team)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team: {str(e)}",
        )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a team.

    - **team_id**: The team UUID

    **Note**: This will fail if there are players associated with the team.
    Remove players first or use cascade delete.
    """
    try:
        # Get team
        result = await session.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {team_id} not found",
            )

        # Check if team has players
        players_result = await session.execute(
            select(func.count()).select_from(Player).where(Player.team_id == team_id)
        )
        players_count = players_result.scalar()

        if players_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete team with {players_count} players. Remove players first.",
            )

        # Delete team
        await session.delete(team)
        await session.commit()

        logger.info(f"Deleted team: {team.name} (id={team.id})")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete team: {str(e)}",
        )


# ============================================
# TEAM BUSINESS ENDPOINTS
# ============================================


@router.get("/{team_id}/players", response_model=list[TeamPlayerResponse], status_code=status.HTTP_200_OK)
async def get_team_players(
    team_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by player status"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get all players in a team.

    - **team_id**: The team UUID
    - **status_filter**: Filter by player status (e.g., active, injured, suspended)
    """
    try:
        # Verify team exists
        team_result = await session.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id {team_id} not found",
            )

        # Get players
        query = select(Player).where(Player.team_id == team_id)

        if status_filter:
            query = query.where(Player.status == status_filter)

        query = query.order_by(Player.jersey_number.asc().nullslast(), Player.last_name.asc())

        result = await session.execute(query)
        players = result.scalars().all()

        return [TeamPlayerResponse.model_validate(player) for player in players]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team players for team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team players: {str(e)}",
        )


@router.get("/{team_id}/stats", response_model=TeamStatsResponse, status_code=status.HTTP_200_OK)
async def get_team_stats(
    team_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get comprehensive statistics for a team.

    Returns:
    - Total number of players
    - Average age of players
    - Total training sessions
    - Total matches played
    - Active injuries count
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

        # Count players
        players_result = await session.execute(
            select(func.count()).select_from(Player).where(Player.team_id == team_id)
        )
        players_count = players_result.scalar() or 0

        # Calculate average age (if birth dates exist)
        avg_age_result = await session.execute(
            select(func.avg(func.extract("year", func.age(Player.date_of_birth))))
            .select_from(Player)
            .where(Player.team_id == team_id)
            .where(Player.date_of_birth.isnot(None))
        )
        avg_age = avg_age_result.scalar()

        # Count training sessions
        sessions_result = await session.execute(
            select(func.count())
            .select_from(TrainingSession)
            .where(TrainingSession.team_id == team_id)
        )
        total_sessions = sessions_result.scalar() or 0

        # Count matches (home or away)
        matches_result = await session.execute(
            select(func.count())
            .select_from(Match)
            .where((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        )
        total_matches = matches_result.scalar() or 0

        # Count active injuries
        injuries_result = await session.execute(
            select(func.count())
            .select_from(Injury)
            .join(Player, Injury.player_id == Player.id)
            .where(Player.team_id == team_id)
            .where(Injury.return_date.is_(None))  # Active injuries have no return date
        )
        active_injuries = injuries_result.scalar() or 0

        return TeamStatsResponse(
            team_id=team.id,
            team_name=team.name,
            players_count=players_count,
            avg_age=round(avg_age, 1) if avg_age else None,
            total_training_sessions=total_sessions,
            total_matches=total_matches,
            active_injuries=active_injuries,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team stats for team {team_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team stats: {str(e)}",
        )


# ============================================
# SEASONS CRUD ENDPOINTS
# ============================================


@router.get("/seasons/", response_model=list[SeasonWithTeams], status_code=status.HTTP_200_OK)
async def list_seasons(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all seasons with teams count.

    - **organization_id**: Filter by organization (multi-tenant support)
    - **is_active**: Filter by active status
    """
    try:
        query = select(Season)

        if organization_id:
            query = query.where(Season.organization_id == organization_id)
        if is_active is not None:
            query = query.where(Season.is_active == is_active)

        query = query.order_by(Season.start_date.desc())

        result = await session.execute(query)
        seasons = result.scalars().all()

        # Get teams count for each season
        seasons_with_teams = []
        for season in seasons:
            teams_result = await session.execute(
                select(func.count()).select_from(Team).where(Team.season_id == season.id)
            )
            teams_count = teams_result.scalar() or 0

            season_dict = SeasonResponse.model_validate(season).model_dump()
            season_dict["teams_count"] = teams_count
            seasons_with_teams.append(SeasonWithTeams(**season_dict))

        return seasons_with_teams

    except Exception as e:
        logger.error(f"Error listing seasons: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list seasons: {str(e)}",
        )


@router.post("/seasons/", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    season_data: SeasonCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new season.

    - **name**: Season name (e.g., "2024-2025")
    - **start_date**: Season start date
    - **end_date**: Season end date
    - **organization_id**: Organization ID (required)
    """
    try:
        # Validate dates
        if season_data.end_date <= season_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )

        # Create season
        season = Season(**season_data.model_dump())

        session.add(season)
        await session.commit()
        await session.refresh(season)

        logger.info(f"Created season: {season.name} (id={season.id})")

        return SeasonResponse.model_validate(season)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating season: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create season: {str(e)}",
        )


@router.put("/seasons/{season_id}", response_model=SeasonResponse, status_code=status.HTTP_200_OK)
async def update_season(
    season_id: UUID,
    season_data: SeasonUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing season.

    - **season_id**: The season UUID
    """
    try:
        # Get season
        result = await session.execute(select(Season).where(Season.id == season_id))
        season = result.scalar_one_or_none()

        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Season with id {season_id} not found",
            )

        # Update season fields
        update_data = season_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(season, key, value)

        # Validate dates if both are set
        if season.end_date <= season.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )

        await session.commit()
        await session.refresh(season)

        logger.info(f"Updated season: {season.name} (id={season.id})")

        return SeasonResponse.model_validate(season)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating season {season_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update season: {str(e)}",
        )

"""Advanced tracking API router - Performance snapshots, goals, match stats, readiness, insights."""

from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.advanced_tracking import (
    AutomatedInsight,
    DailyReadiness,
    MatchPlayerStats,
    PerformanceSnapshot,
    PlayerGoal,
)
from app.models.player import Player
from app.models.user import User
from app.schemas.advanced_tracking import (
    AutomatedInsightCreate,
    AutomatedInsightResponse,
    AutomatedInsightUpdate,
    DailyReadinessCreate,
    DailyReadinessResponse,
    DailyReadinessUpdate,
    MatchPlayerStatsCreate,
    MatchPlayerStatsResponse,
    MatchPlayerStatsUpdate,
    PerformanceSnapshotCreate,
    PerformanceSnapshotResponse,
    PerformanceSnapshotUpdate,
    PlayerGoalCreate,
    PlayerGoalResponse,
    PlayerGoalUpdate,
)

router = APIRouter()


# ===== Performance Snapshots =====


@router.post("/snapshots", response_model=PerformanceSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_performance_snapshot(
    snapshot_data: PerformanceSnapshotCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new performance snapshot."""
    # Verify player belongs to organization
    result = await session.execute(
        select(Player).where(
            Player.id == snapshot_data.player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    snapshot = PerformanceSnapshot(**snapshot_data.model_dump(), organization_id=current_user.organization_id)
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


@router.get("/snapshots", response_model=list[PerformanceSnapshotResponse])
async def list_performance_snapshots(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None, description="Filter by player ID"),
    period_type: str | None = Query(None, description="Filter by period type (WEEKLY, MONTHLY)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List performance snapshots with optional filters."""
    query = select(PerformanceSnapshot).where(PerformanceSnapshot.organization_id == current_user.organization_id)

    if player_id:
        query = query.where(PerformanceSnapshot.player_id == player_id)
    if period_type:
        query = query.where(PerformanceSnapshot.period_type == period_type)

    query = query.offset(skip).limit(limit).order_by(PerformanceSnapshot.snapshot_date.desc())

    result = await session.execute(query)
    snapshots = result.scalars().all()
    return snapshots


@router.get("/snapshots/{snapshot_id}", response_model=PerformanceSnapshotResponse)
async def get_performance_snapshot(
    snapshot_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific performance snapshot."""
    result = await session.execute(
        select(PerformanceSnapshot).where(
            PerformanceSnapshot.id == snapshot_id,
            PerformanceSnapshot.organization_id == current_user.organization_id
        )
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")

    return snapshot


@router.patch("/snapshots/{snapshot_id}", response_model=PerformanceSnapshotResponse)
async def update_performance_snapshot(
    snapshot_id: UUID,
    snapshot_data: PerformanceSnapshotUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a performance snapshot."""
    result = await session.execute(
        select(PerformanceSnapshot).where(
            PerformanceSnapshot.id == snapshot_id,
            PerformanceSnapshot.organization_id == current_user.organization_id
        )
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")

    update_data = snapshot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(snapshot, field, value)

    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


# ===== Player Goals =====


@router.post("/goals", response_model=PlayerGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_player_goal(
    goal_data: PlayerGoalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new player goal."""
    # Verify player belongs to organization
    result = await session.execute(
        select(Player).where(
            Player.id == goal_data.player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Calculate days remaining
    days_remaining = (goal_data.target_date - date.today()).days

    goal = PlayerGoal(
        **goal_data.model_dump(),
        organization_id=current_user.organization_id,
        days_remaining=days_remaining
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


@router.get("/goals", response_model=list[PlayerGoalResponse])
async def list_player_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None, description="Filter by player ID"),
    status_filter: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List player goals with optional filters."""
    query = select(PlayerGoal).where(PlayerGoal.organization_id == current_user.organization_id)

    if player_id:
        query = query.where(PlayerGoal.player_id == player_id)
    if status_filter:
        query = query.where(PlayerGoal.status == status_filter)
    if category:
        query = query.where(PlayerGoal.category == category)

    query = query.offset(skip).limit(limit).order_by(PlayerGoal.target_date)

    result = await session.execute(query)
    goals = result.scalars().all()
    return goals


@router.get("/goals/{goal_id}", response_model=PlayerGoalResponse)
async def get_player_goal(
    goal_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific player goal."""
    result = await session.execute(
        select(PlayerGoal).where(
            PlayerGoal.id == goal_id,
            PlayerGoal.organization_id == current_user.organization_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    return goal


@router.patch("/goals/{goal_id}", response_model=PlayerGoalResponse)
async def update_player_goal(
    goal_id: UUID,
    goal_data: PlayerGoalUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a player goal."""
    result = await session.execute(
        select(PlayerGoal).where(
            PlayerGoal.id == goal_id,
            PlayerGoal.organization_id == current_user.organization_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    update_data = goal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    # Recalculate days remaining if target_date changed
    if "target_date" in update_data:
        goal.days_remaining = (goal.target_date - date.today()).days

    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


# ===== Match Player Stats =====


@router.post("/match-stats", response_model=MatchPlayerStatsResponse, status_code=status.HTTP_201_CREATED)
async def create_match_player_stats(
    stats_data: MatchPlayerStatsCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create match player statistics."""
    # Verify player belongs to organization
    result = await session.execute(
        select(Player).where(
            Player.id == stats_data.player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    stats = MatchPlayerStats(**stats_data.model_dump(), organization_id=current_user.organization_id)
    session.add(stats)
    await session.commit()
    await session.refresh(stats)
    return stats


@router.get("/match-stats", response_model=list[MatchPlayerStatsResponse])
async def list_match_player_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None, description="Filter by player ID"),
    match_id: UUID | None = Query(None, description="Filter by match ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List match player stats with optional filters."""
    query = select(MatchPlayerStats).where(MatchPlayerStats.organization_id == current_user.organization_id)

    if player_id:
        query = query.where(MatchPlayerStats.player_id == player_id)
    if match_id:
        query = query.where(MatchPlayerStats.match_id == match_id)

    query = query.offset(skip).limit(limit).order_by(MatchPlayerStats.match_date.desc())

    result = await session.execute(query)
    stats = result.scalars().all()
    return stats


@router.get("/match-stats/{stats_id}", response_model=MatchPlayerStatsResponse)
async def get_match_player_stats(
    stats_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get specific match player stats."""
    result = await session.execute(
        select(MatchPlayerStats).where(
            MatchPlayerStats.id == stats_id,
            MatchPlayerStats.organization_id == current_user.organization_id
        )
    )
    stats = result.scalar_one_or_none()

    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match stats not found")

    return stats


@router.patch("/match-stats/{stats_id}", response_model=MatchPlayerStatsResponse)
async def update_match_player_stats(
    stats_id: UUID,
    stats_data: MatchPlayerStatsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update match player stats."""
    result = await session.execute(
        select(MatchPlayerStats).where(
            MatchPlayerStats.id == stats_id,
            MatchPlayerStats.organization_id == current_user.organization_id
        )
    )
    stats = result.scalar_one_or_none()

    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match stats not found")

    update_data = stats_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stats, field, value)

    session.add(stats)
    await session.commit()
    await session.refresh(stats)
    return stats


# ===== Daily Readiness =====


@router.post("/readiness", response_model=DailyReadinessResponse, status_code=status.HTTP_201_CREATED)
async def create_daily_readiness(
    readiness_data: DailyReadinessCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create daily readiness score."""
    # Verify player belongs to organization
    result = await session.execute(
        select(Player).where(
            Player.id == readiness_data.player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    readiness = DailyReadiness(**readiness_data.model_dump(), organization_id=current_user.organization_id)
    session.add(readiness)
    await session.commit()
    await session.refresh(readiness)
    return readiness


@router.get("/readiness", response_model=list[DailyReadinessResponse])
async def list_daily_readiness(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None, description="Filter by player ID"),
    date_from: date | None = Query(None, description="Filter from date"),
    date_to: date | None = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List daily readiness scores with optional filters."""
    query = select(DailyReadiness).where(DailyReadiness.organization_id == current_user.organization_id)

    if player_id:
        query = query.where(DailyReadiness.player_id == player_id)
    if date_from:
        query = query.where(DailyReadiness.date >= date_from)
    if date_to:
        query = query.where(DailyReadiness.date <= date_to)

    query = query.offset(skip).limit(limit).order_by(DailyReadiness.date.desc())

    result = await session.execute(query)
    readiness_list = result.scalars().all()
    return readiness_list


@router.get("/readiness/{readiness_id}", response_model=DailyReadinessResponse)
async def get_daily_readiness(
    readiness_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get specific daily readiness score."""
    result = await session.execute(
        select(DailyReadiness).where(
            DailyReadiness.id == readiness_id,
            DailyReadiness.organization_id == current_user.organization_id
        )
    )
    readiness = result.scalar_one_or_none()

    if not readiness:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Readiness score not found")

    return readiness


@router.patch("/readiness/{readiness_id}", response_model=DailyReadinessResponse)
async def update_daily_readiness(
    readiness_id: UUID,
    readiness_data: DailyReadinessUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update daily readiness score."""
    result = await session.execute(
        select(DailyReadiness).where(
            DailyReadiness.id == readiness_id,
            DailyReadiness.organization_id == current_user.organization_id
        )
    )
    readiness = result.scalar_one_or_none()

    if not readiness:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Readiness score not found")

    update_data = readiness_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(readiness, field, value)

    session.add(readiness)
    await session.commit()
    await session.refresh(readiness)
    return readiness


# ===== Automated Insights =====


@router.post("/insights", response_model=AutomatedInsightResponse, status_code=status.HTTP_201_CREATED)
async def create_automated_insight(
    insight_data: AutomatedInsightCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create an automated insight."""
    insight = AutomatedInsight(**insight_data.model_dump(), organization_id=current_user.organization_id)
    session.add(insight)
    await session.commit()
    await session.refresh(insight)
    return insight


@router.get("/insights", response_model=list[AutomatedInsightResponse])
async def list_automated_insights(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None, description="Filter by player ID"),
    team_id: UUID | None = Query(None, description="Filter by team ID"),
    priority: str | None = Query(None, description="Filter by priority"),
    insight_type: str | None = Query(None, description="Filter by type"),
    is_read: bool | None = Query(None, description="Filter by read status"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List automated insights with optional filters."""
    query = select(AutomatedInsight).where(AutomatedInsight.organization_id == current_user.organization_id)

    if player_id:
        query = query.where(AutomatedInsight.player_id == player_id)
    if team_id:
        query = query.where(AutomatedInsight.team_id == team_id)
    if priority:
        query = query.where(AutomatedInsight.priority == priority)
    if insight_type:
        query = query.where(AutomatedInsight.insight_type == insight_type)
    if is_read is not None:
        query = query.where(AutomatedInsight.is_read == is_read)
    if is_active is not None:
        query = query.where(AutomatedInsight.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(AutomatedInsight.created_at.desc())

    result = await session.execute(query)
    insights = result.scalars().all()
    return insights


@router.get("/insights/{insight_id}", response_model=AutomatedInsightResponse)
async def get_automated_insight(
    insight_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get specific automated insight."""
    result = await session.execute(
        select(AutomatedInsight).where(
            AutomatedInsight.id == insight_id,
            AutomatedInsight.organization_id == current_user.organization_id
        )
    )
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    return insight


@router.patch("/insights/{insight_id}", response_model=AutomatedInsightResponse)
async def update_automated_insight(
    insight_id: UUID,
    insight_data: AutomatedInsightUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update an automated insight (mark as read, dismissed, add feedback)."""
    result = await session.execute(
        select(AutomatedInsight).where(
            AutomatedInsight.id == insight_id,
            AutomatedInsight.organization_id == current_user.organization_id
        )
    )
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    update_data = insight_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(insight, field, value)

    session.add(insight)
    await session.commit()
    await session.refresh(insight)
    return insight


@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automated_insight(
    insight_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete an automated insight."""
    result = await session.execute(
        select(AutomatedInsight).where(
            AutomatedInsight.id == insight_id,
            AutomatedInsight.organization_id == current_user.organization_id
        )
    )
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    await session.delete(insight)
    await session.commit()
    return None

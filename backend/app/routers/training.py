"""Training API router for RPE tracking and session load management."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.player_session import PlayerSession
from app.models.session import TrainingSession
from app.schemas.training import (
    RpeUpsertPayload,
    RpeUpsertResponse,
    WeeklyLoadPoint,
    WeeklyLoadResponse,
)

router = APIRouter()


async def get_demo_org_id(session: AsyncSession) -> UUID:
    """Get the first organization ID for demo purposes (no auth)."""
    from app.models.organization import Organization
    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise HTTPException(status_code=404, detail="No organization found. Please run seed script.")
    return org_id


@router.post("/rpe", response_model=RpeUpsertResponse, status_code=status.HTTP_200_OK)
async def upsert_rpe(
    payload: RpeUpsertPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Upsert RPE (Rate of Perceived Exertion) for a player session.

    Calculates session_load = rpe × duration_min and stores both values.
    If the record exists, it updates; otherwise, it creates a new one.
    """
    # Validate session exists and get duration
    session_result = await session.execute(
        select(TrainingSession).where(TrainingSession.id == payload.session_id)
    )
    training_session = session_result.scalar_one_or_none()

    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training session {payload.session_id} not found"
        )

    if training_session.duration_min is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Training session {payload.session_id} has no duration_min"
        )

    # Calculate session load
    session_load = payload.rpe * Decimal(training_session.duration_min)

    # Check if player_session already exists
    ps_result = await session.execute(
        select(PlayerSession).where(
            PlayerSession.player_id == payload.player_id,
            PlayerSession.session_id == payload.session_id
        )
    )
    player_session = ps_result.scalar_one_or_none()

    now = datetime.utcnow()

    if player_session:
        # Update existing
        player_session.rpe = payload.rpe
        player_session.session_load = session_load
        player_session.updated_at = now
        session.add(player_session)
    else:
        # Create new
        player_session = PlayerSession(
            player_id=payload.player_id,
            session_id=payload.session_id,
            rpe=payload.rpe,
            session_load=session_load,
            created_at=now,
            updated_at=now
        )
        session.add(player_session)

    await session.commit()
    await session.refresh(player_session)

    return RpeUpsertResponse(
        player_id=player_session.player_id,
        session_id=player_session.session_id,
        rpe=player_session.rpe,
        duration_min=training_session.duration_min,
        session_load=player_session.session_load,
        updated_at=player_session.updated_at
    )


@router.get("/players/{player_id}/weekly-load", response_model=WeeklyLoadResponse)
async def get_player_weekly_load(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    weeks: int = Query(8, ge=1, le=16, description="Number of weeks to retrieve (max 16)")
):
    """
    Get weekly training load aggregates for a player over the last N weeks.

    Returns all weeks in the range, including weeks with 0 load.
    Also returns the total load for the current week.
    """
    # Calculate week range
    today = date.today()
    # Get the Monday of current week
    current_week_start = today - timedelta(days=today.weekday())
    # Calculate the start of the range (N weeks ago)
    range_start = current_week_start - timedelta(weeks=weeks - 1)

    # Generate all week starts in the range
    all_weeks = []
    week_cursor = range_start
    while week_cursor <= current_week_start:
        all_weeks.append(week_cursor)
        week_cursor += timedelta(weeks=1)

    # Query actual data from the view
    query = text("""
        SELECT
            week_start,
            weekly_load
        FROM vw_player_weekly_load
        WHERE player_id = :player_id
          AND week_start >= :range_start
          AND week_start <= :current_week_start
        ORDER BY week_start ASC
    """)

    result = await session.execute(
        query,
        {
            "player_id": str(player_id),
            "range_start": range_start,
            "current_week_start": current_week_start
        }
    )
    rows = result.fetchall()

    # Create a map of week_start -> weekly_load
    load_map = {row[0]: Decimal(row[1]) for row in rows}

    # Fill in all weeks (including 0s)
    weekly_data = []
    for week in all_weeks:
        weekly_data.append(
            WeeklyLoadPoint(
                week_start=week,
                weekly_load=load_map.get(week, Decimal(0))
            )
        )

    # Get current week total
    current_week_total = load_map.get(current_week_start, Decimal(0))

    return WeeklyLoadResponse(
        player_id=player_id,
        weeks=weekly_data,
        total_current_week=current_week_total
    )

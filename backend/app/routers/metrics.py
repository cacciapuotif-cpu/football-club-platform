"""
Metrics API router for player load metrics and readiness tracking.

Endpoints for ACWR, Monotony, Strain, and Readiness Index.
"""

from datetime import date, timedelta
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.jobs.calc_metrics import update_player_metrics
from app.schemas.metrics import (
    MetricDaily,
    PlayerMetricsSummary,
    PlayerMetricsLatest
)

router = APIRouter()


@router.get("/player/{player_id}/summary", response_model=PlayerMetricsSummary)
async def get_player_metrics_summary(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = 30
):
    """
    Get player metrics summary for the last N days.

    Returns ACWR, Monotony, Strain, and Readiness for each day.
    Default is 30 days.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    query = text("""
        SELECT
            date,
            acwr,
            monotony,
            strain,
            readiness
        FROM player_metrics_daily
        WHERE player_id = :player_id
          AND date >= :start_date
          AND date <= :end_date
        ORDER BY date ASC
    """)

    result = await session.execute(
        query,
        {
            "player_id": str(player_id),
            "start_date": start_date,
            "end_date": end_date
        }
    )
    rows = result.fetchall()

    metrics = [
        MetricDaily(
            date=row[0],
            acwr=float(row[1]) if row[1] is not None else None,
            monotony=float(row[2]) if row[2] is not None else None,
            strain=float(row[3]) if row[3] is not None else None,
            readiness=float(row[4]) if row[4] is not None else None
        )
        for row in rows
    ]

    return PlayerMetricsSummary(
        player_id=player_id,
        metrics=metrics
    )


@router.get("/player/{player_id}/latest", response_model=PlayerMetricsLatest)
async def get_player_metrics_latest(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Get the latest metrics record for a player.

    Returns the most recent ACWR, Monotony, Strain, and Readiness.
    """
    query = text("""
        SELECT
            date,
            acwr,
            monotony,
            strain,
            readiness
        FROM player_metrics_daily
        WHERE player_id = :player_id
        ORDER BY date DESC
        LIMIT 1
    """)

    result = await session.execute(
        query,
        {"player_id": str(player_id)}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for player {player_id}"
        )

    return PlayerMetricsLatest(
        player_id=player_id,
        date=row[0],
        acwr=float(row[1]) if row[1] is not None else None,
        monotony=float(row[2]) if row[2] is not None else None,
        strain=float(row[3]) if row[3] is not None else None,
        readiness=float(row[4]) if row[4] is not None else None
    )


@router.post("/recalculate", status_code=status.HTTP_202_ACCEPTED)
async def recalculate_metrics():
    """
    Manually trigger metrics recalculation for all players.

    This endpoint is typically used by admins or for testing.
    In production, this runs automatically via scheduled job.
    """
    # Run the job asynchronously
    await update_player_metrics()

    return {
        "status": "success",
        "message": "Metrics recalculation triggered successfully"
    }

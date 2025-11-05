"""
Progress tracking endpoints for player development.
Provides aggregated metrics over time with flexible bucketing.
"""

from datetime import date, datetime, timedelta
from typing import List, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()


class ProgressBucket(BaseModel):
    """Single time bucket with aggregated metric."""
    bucket: date | datetime
    metric_key: str
    avg_value: float
    min_value: float | None = None
    max_value: float | None = None
    count: int
    completeness_pct: float | None = None


class TrainingLoadPoint(BaseModel):
    """Training load data point with ACWR."""
    date: date
    minutes: float
    rpe_post: float
    hsr: float
    total_distance: float | None
    srpe: float
    acute_7d: float | None
    chronic_28d: float | None
    acwr_7_28: float | None


class MetricSummary(BaseModel):
    """Summary statistics for a metric."""
    metric_key: str
    current_value: float | None
    avg_value: float
    trend_pct: float | None  # % change vs previous period
    variance: float
    min_value: float
    max_value: float
    completeness_pct: float


class PlayerOverview(BaseModel):
    """Player overview with KPIs."""
    player_id: UUID
    period_days: int
    wellness_entries: int
    training_sessions: int
    matches: int
    wellness_completeness_pct: float
    training_completeness_pct: float
    metric_summaries: List[MetricSummary]
    data_quality_issues: int


@router.get("/players/{player_id}/progress", response_model=List[ProgressBucket])
async def get_player_progress(
    player_id: UUID,
    metrics: List[str] = Query(..., description="Comma-separated metric keys, e.g., stress,doms,sleep_quality"),
    date_from: date = Query(..., alias="from"),
    date_to: date = Query(..., alias="to"),
    groupby: Literal["day", "week", "month"] = Query("week"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player progress for specified metrics over time.

    Returns aggregated values bucketed by day/week/month.
    """

    # Map groupby to SQL date_trunc
    bucket_map = {"day": "day", "week": "week", "month": "month"}
    bucket_sql = bucket_map[groupby]

    query = text("""
        SELECT
            date_trunc(:bucket, ws.date) AS bucket,
            wm.metric_key,
            AVG(wm.metric_value) AS avg_value,
            MIN(wm.metric_value) AS min_value,
            MAX(wm.metric_value) AS max_value,
            COUNT(*) AS count
        FROM wellness_sessions ws
        JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND ws.date BETWEEN :date_from AND :date_to
          AND wm.metric_key = ANY(:metrics)
          AND wm.validity = 'valid'
        GROUP BY bucket, wm.metric_key
        ORDER BY bucket ASC, wm.metric_key
    """)

    result = await session.execute(
        query,
        {
            "bucket": bucket_sql,
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "metrics": metrics,
        }
    )

    rows = result.fetchall()

    return [
        ProgressBucket(
            bucket=row[0],
            metric_key=row[1],
            avg_value=float(row[2]),
            min_value=float(row[3]) if row[3] is not None else None,
            max_value=float(row[4]) if row[4] is not None else None,
            count=int(row[5]),
        )
        for row in rows
    ]


@router.get("/players/{player_id}/training-load", response_model=List[TrainingLoadPoint])
async def get_training_load(
    player_id: UUID,
    date_from: date = Query(..., alias="from"),
    date_to: date = Query(..., alias="to"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get training load data with sRPE and ACWR (Acute:Chronic Workload Ratio).

    - sRPE = RPE * minutes
    - ACWR = 7-day rolling average / 28-day rolling average
    """

    query = text("""
    WITH base AS (
        SELECT
            ts.session_date::date AS date,
            COALESCE(ta.minutes, 0) AS minutes,
            COALESCE(ta.rpe_post, 0) AS rpe_post,
            COALESCE(MAX(CASE WHEN tm.metric_key='hsr' THEN tm.metric_value END), 0) AS hsr,
            COALESCE(MAX(CASE WHEN tm.metric_key='total_distance' THEN tm.metric_value END), 0) AS total_distance
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        LEFT JOIN training_metrics tm ON tm.training_attendance_id = ta.id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date BETWEEN :date_from AND :date_to
        GROUP BY ts.session_date::date, ta.minutes, ta.rpe_post
    ),
    with_srpe AS (
        SELECT
            date,
            minutes,
            rpe_post,
            hsr,
            total_distance,
            rpe_post * minutes AS srpe
        FROM base
    ),
    with_rolling AS (
        SELECT
            date,
            minutes,
            rpe_post,
            hsr,
            total_distance,
            srpe,
            AVG(srpe) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS acute_7d,
            AVG(srpe) OVER (ORDER BY date ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) AS chronic_28d
        FROM with_srpe
    )
    SELECT
        date,
        minutes,
        rpe_post,
        hsr,
        total_distance,
        srpe,
        acute_7d,
        chronic_28d,
        CASE
            WHEN chronic_28d IS NULL OR chronic_28d = 0 THEN NULL
            ELSE acute_7d / chronic_28d
        END AS acwr_7_28
    FROM with_rolling
    ORDER BY date ASC
    """)

    result = await session.execute(
        query,
        {
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
        }
    )

    rows = result.fetchall()

    return [
        TrainingLoadPoint(
            date=row[0],
            minutes=float(row[1]),
            rpe_post=float(row[2]),
            hsr=float(row[3]),
            total_distance=float(row[4]) if row[4] else None,
            srpe=float(row[5]),
            acute_7d=float(row[6]) if row[6] is not None else None,
            chronic_28d=float(row[7]) if row[7] is not None else None,
            acwr_7_28=float(row[8]) if row[8] is not None else None,
        )
        for row in rows
    ]


@router.get("/players/{player_id}/overview", response_model=PlayerOverview)
async def get_player_overview(
    player_id: UUID,
    period: Literal["7d", "30d", "90d", "season"] = "30d",
    metrics: List[str] = Query(default=["sleep_quality", "stress", "fatigue", "doms", "mood"]),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player overview with KPIs and data completeness.

    Includes:
    - Data completeness %
    - Metric summaries (avg, trend, variance)
    - Data quality issues
    """

    # Map period to days
    period_map = {"7d": 7, "30d": 30, "90d": 90, "season": 180}
    days = period_map[period]
    date_from = datetime.now().date() - timedelta(days=days)
    date_to = datetime.now().date()

    # Wellness entries count
    wellness_query = text("""
        SELECT COUNT(DISTINCT ws.id)::int
        FROM wellness_sessions ws
        WHERE ws.player_id = :player_id
          AND ws.date >= :date_from
    """)
    wellness_result = await session.execute(wellness_query, {"player_id": player_id, "date_from": date_from})
    wellness_count = wellness_result.scalar() or 0

    # Training sessions count
    training_query = text("""
        SELECT COUNT(DISTINCT ta.training_session_id)::int
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date >= :date_from
    """)
    training_result = await session.execute(training_query, {"player_id": player_id, "date_from": date_from})
    training_count = training_result.scalar() or 0

    # Matches count
    matches_query = text("""
        SELECT COUNT(DISTINCT a.match_id)::int
        FROM attendances a
        JOIN matches m ON m.id = a.match_id
        WHERE a.player_id = :player_id
          AND m.match_date::date >= :date_from
    """)
    matches_result = await session.execute(matches_query, {"player_id": player_id, "date_from": date_from})
    matches_count = matches_result.scalar() or 0

    # Completeness %
    wellness_completeness = (wellness_count / days) * 100 if days > 0 else 0
    training_completeness = (training_count / (days / 7)) * 100 if days > 0 else 0  # ~1 session per week expected

    # Metric summaries
    summaries = []
    for metric_key in metrics:
        metric_query = text("""
            WITH recent AS (
                SELECT wm.metric_value
                FROM wellness_sessions ws
                JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
                WHERE ws.player_id = :player_id
                  AND ws.date >= :date_from
                  AND wm.metric_key = :metric_key
                  AND wm.validity = 'valid'
            ),
            previous AS (
                SELECT AVG(wm.metric_value) AS prev_avg
                FROM wellness_sessions ws
                JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
                WHERE ws.player_id = :player_id
                  AND ws.date BETWEEN :prev_from AND :prev_to
                  AND wm.metric_key = :metric_key
                  AND wm.validity = 'valid'
            )
            SELECT
                (SELECT metric_value FROM recent ORDER BY metric_value DESC LIMIT 1) AS current_value,
                AVG(metric_value) AS avg_value,
                VARIANCE(metric_value) AS variance,
                MIN(metric_value) AS min_value,
                MAX(metric_value) AS max_value,
                COUNT(*)::int AS count,
                (SELECT prev_avg FROM previous) AS prev_avg
            FROM recent
        """)

        prev_from = date_from - timedelta(days=days)
        prev_to = date_from - timedelta(days=1)

        metric_result = await session.execute(
            metric_query,
            {
                "player_id": player_id,
                "date_from": date_from,
                "metric_key": metric_key,
                "prev_from": prev_from,
                "prev_to": prev_to,
            }
        )
        row = metric_result.fetchone()

        if row and row[1] is not None:
            current_value = float(row[0]) if row[0] else None
            avg_value = float(row[1])
            variance = float(row[2]) if row[2] else 0
            min_value = float(row[3])
            max_value = float(row[4])
            count = int(row[5])
            prev_avg = float(row[6]) if row[6] else None

            # Calculate trend %
            trend_pct = None
            if prev_avg and prev_avg > 0:
                trend_pct = ((avg_value - prev_avg) / prev_avg) * 100

            completeness_pct = (count / days) * 100 if days > 0 else 0

            summaries.append(
                MetricSummary(
                    metric_key=metric_key,
                    current_value=current_value,
                    avg_value=avg_value,
                    trend_pct=trend_pct,
                    variance=variance,
                    min_value=min_value,
                    max_value=max_value,
                    completeness_pct=completeness_pct,
                )
            )

    # Data quality issues
    dq_query = text("""
        SELECT COUNT(*)::int
        FROM data_quality_logs
        WHERE entity_id = :player_id
          AND detected_at >= :date_from
          AND resolved = false
    """)
    dq_result = await session.execute(dq_query, {"player_id": player_id, "date_from": date_from})
    dq_count = dq_result.scalar() or 0

    return PlayerOverview(
        player_id=player_id,
        period_days=days,
        wellness_entries=wellness_count,
        training_sessions=training_count,
        matches=matches_count,
        wellness_completeness_pct=min(wellness_completeness, 100),
        training_completeness_pct=min(training_completeness, 100),
        metric_summaries=summaries,
        data_quality_issues=dq_count,
    )

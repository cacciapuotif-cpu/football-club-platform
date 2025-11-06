"""
Progress tracking endpoints for player development.
Provides aggregated metrics over time with flexible bucketing, ACWR, and overview KPIs.
"""

from datetime import date, datetime, timedelta
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()

# Standard wellness metrics
DEFAULT_WELLNESS_METRICS = [
    "sleep_quality", "sleep_hours", "stress", "fatigue", "soreness", "mood", 
    "motivation", "hydration", "rpe_morning", "body_weight_kg", "resting_hr_bpm", "hrv_ms"
]

# Training metrics
DEFAULT_TRAINING_METRICS = [
    "rpe_post", "hsr", "sprint_count", "total_distance", "accel_count", 
    "decel_count", "top_speed", "avg_hr", "max_hr", "player_load"
]

# Match metrics
DEFAULT_MATCH_METRICS = [
    "pass_accuracy", "pass_completed", "duels_won", "touches", 
    "dribbles_success", "interceptions", "tackles", "shots_on_target"
]


class ProgressSeriesPoint(BaseModel):
    """Single bucket in progress series."""
    bucket_start: date
    sleep_quality: Optional[float] = None
    fatigue: Optional[float] = None
    soreness: Optional[float] = None
    stress: Optional[float] = None
    mood: Optional[float] = None
    srpe: Optional[float] = None
    delta_prev_pct: Optional[dict[str, float]] = None


class ProgressResponse(BaseModel):
    """Response for progress endpoint."""
    bucket: Literal["daily", "weekly", "monthly"]
    date_from: date
    date_to: date
    series: list[ProgressSeriesPoint]


class TrainingLoadPoint(BaseModel):
    """Single point in training load series."""
    date: date
    srpe: float
    acute: Optional[float] = None
    chronic: Optional[float] = None
    acwr: Optional[float] = None


class TrainingLoadResponse(BaseModel):
    """Response for training-load endpoint."""
    series: list[TrainingLoadPoint]
    acute_days: int
    chronic_days: int
    flags: list[dict] = []


class PlayerOverviewResponse(BaseModel):
    """Response for overview endpoint."""
    window_days: int
    wellness_days_with_data: int
    wellness_completeness_pct: float
    last_values: dict[str, Optional[float]]
    training_sessions: int
    present_count: int
    avg_srpe_last_7d: Optional[float] = None
    avg_srpe_last_28d: Optional[float] = None


@router.get("/players/{player_id}/progress", response_model=ProgressResponse)
async def get_player_progress(
    player_id: UUID,
    bucket: Literal["daily", "weekly", "monthly"] = Query("weekly"),
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    metrics: Optional[str] = Query(None, description="Comma-separated metric keys"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player progress metrics aggregated by time bucket.
    
    Returns wellness metrics and sRPE with delta vs previous bucket.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Parse metrics or use defaults
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = DEFAULT_WELLNESS_METRICS
    
    # Map bucket to SQL date_trunc
    bucket_map = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month"
    }
    bucket_sql = bucket_map[bucket]
    
    # Build dynamic query for selected metrics
    metric_cases = []
    for metric in metric_list:
        metric_cases.append(
            f"AVG(CASE WHEN wm.metric_key = '{metric}' THEN wm.metric_value END) AS {metric}"
        )
    
    metrics_select = ",\n            ".join(metric_cases)
    
    # Query wellness metrics by bucket
    wellness_query = text(f"""
        WITH wellness_buckets AS (
            SELECT
                DATE_TRUNC(:bucket_sql, ws.date::timestamp)::date AS bucket_start,
                {metrics_select}
            FROM wellness_sessions ws
            JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
            WHERE ws.player_id = :player_id
              AND ws.date BETWEEN :date_from AND :date_to
              AND wm.metric_key = ANY(:metric_list)
              AND wm.validity = 'valid'
            GROUP BY bucket_start
        )
        SELECT * FROM wellness_buckets
        ORDER BY bucket_start ASC
    """)
    
    wellness_result = await session.execute(
        wellness_query,
        {
            "bucket_sql": bucket_sql,
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "metric_list": metric_list,
        }
    )
    wellness_rows = wellness_result.fetchall()
    
    # Query sRPE by bucket
    srpe_query = text(f"""
        WITH srpe_daily AS (
            SELECT
                ts.session_date::date AS session_date,
                COALESCE(SUM(ta.rpe_post * ta.minutes), 0) AS daily_srpe
            FROM training_attendance ta
            JOIN training_sessions ts ON ts.id = ta.training_session_id
            WHERE ta.player_id = :player_id
              AND ts.session_date::date BETWEEN :date_from AND :date_to
              AND ta.status = 'present'
              AND ta.rpe_post IS NOT NULL
              AND ta.minutes IS NOT NULL
            GROUP BY ts.session_date::date
        )
        SELECT
            DATE_TRUNC(:bucket_sql, session_date::timestamp)::date AS bucket_start,
            SUM(daily_srpe) AS srpe
        FROM srpe_daily
        GROUP BY bucket_start
        ORDER BY bucket_start ASC
    """)
    
    srpe_result = await session.execute(
        srpe_query,
        {
            "bucket_sql": bucket_sql,
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
        }
    )
    srpe_rows = {row[0]: float(row[1]) for row in srpe_result.fetchall()}
    
    # Combine wellness and sRPE data, calculate deltas
    series = []
    prev_bucket_data = None
    
    for row in wellness_rows:
        bucket_start = row[0]
        bucket_data = {
            "bucket_start": bucket_start,
            "srpe": srpe_rows.get(bucket_start),
        }
        
        # Add wellness metrics (columns 1+)
        for i, metric in enumerate(metric_list, start=1):
            bucket_data[metric] = float(row[i]) if row[i] is not None else None
        
        # Calculate delta vs previous bucket
        delta_prev_pct = {}
        if prev_bucket_data:
            for metric in metric_list:
                curr_val = bucket_data.get(metric)
                prev_val = prev_bucket_data.get(metric)
                if curr_val is not None and prev_val is not None and prev_val != 0:
                    delta_pct = ((curr_val - prev_val) / prev_val) * 100
                    delta_prev_pct[metric] = round(delta_pct, 2)
            
            # Delta for sRPE
            curr_srpe = bucket_data.get("srpe")
            prev_srpe = prev_bucket_data.get("srpe")
            if curr_srpe is not None and prev_srpe is not None and prev_srpe != 0:
                delta_prev_pct["srpe"] = round(((curr_srpe - prev_srpe) / prev_srpe) * 100, 2)
        
        bucket_data["delta_prev_pct"] = delta_prev_pct if delta_prev_pct else None
        series.append(ProgressSeriesPoint(**bucket_data))
        prev_bucket_data = bucket_data
    
    return ProgressResponse(
        bucket=bucket,
        date_from=date_from,
        date_to=date_to,
        series=series,
    )


@router.get("/players/{player_id}/training-load", response_model=TrainingLoadResponse)
async def get_training_load(
    player_id: UUID,
    acute_days: int = Query(7, ge=1, le=14),
    chronic_days: int = Query(28, ge=7, le=56),
    session: AsyncSession = Depends(get_session),
):
    """
    Get training load with ACWR (Acute:Chronic Workload Ratio).
    
    - sRPE = RPE * minutes per day
    - acute = rolling average of last N days
    - chronic = rolling average of last M days
    - ACWR = acute / chronic
    - Flags: high if ACWR > 1.5, low if ACWR < 0.8
    """
    # Get daily sRPE for last chronic_days + buffer
    date_from = date.today() - timedelta(days=chronic_days + 7)
    date_to = date.today()
    
    query = text("""
        WITH daily_srpe AS (
            SELECT
                ts.session_date::date AS date,
                COALESCE(SUM(ta.rpe_post * ta.minutes), 0) AS srpe
            FROM training_attendance ta
            JOIN training_sessions ts ON ts.id = ta.training_session_id
            WHERE ta.player_id = :player_id
              AND ts.session_date::date BETWEEN :date_from AND :date_to
              AND ta.status = 'present'
              AND ta.rpe_post IS NOT NULL
              AND ta.minutes IS NOT NULL
            GROUP BY ts.session_date::date
        ),
        all_days AS (
            SELECT generate_series(:date_from::date, :date_to::date, '1 day'::interval)::date AS date
        ),
        filled_srpe AS (
            SELECT
                ad.date,
                COALESCE(ds.srpe, 0) AS srpe
            FROM all_days ad
            LEFT JOIN daily_srpe ds ON ds.date = ad.date
        ),
        with_rolling AS (
            SELECT
                date,
                srpe,
                AVG(srpe) OVER (
                    ORDER BY date
                    ROWS BETWEEN :acute_rows PRECEDING AND CURRENT ROW
                ) AS acute,
                AVG(srpe) OVER (
                    ORDER BY date
                    ROWS BETWEEN :chronic_rows PRECEDING AND CURRENT ROW
                ) AS chronic
            FROM filled_srpe
        )
        SELECT
            date,
            srpe,
            CASE WHEN acute >= :min_acute_rows THEN acute ELSE NULL END AS acute,
            CASE WHEN chronic >= :min_chronic_rows THEN chronic ELSE NULL END AS chronic,
            CASE
                WHEN chronic >= :min_chronic_rows AND chronic > 0
                THEN acute / chronic
                ELSE NULL
            END AS acwr
        FROM with_rolling
        WHERE date >= :date_from + :chronic_days
        ORDER BY date ASC
    """)
    
    acute_rows = acute_days - 1  # ROWS BETWEEN is inclusive
    chronic_rows = chronic_days - 1
    min_acute_rows = max(acute_days - 2, 1)  # Allow some missing days
    min_chronic_rows = max(chronic_days - 5, 1)
    
    result = await session.execute(
        query,
        {
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "acute_rows": acute_rows,
            "chronic_rows": chronic_rows,
            "min_acute_rows": min_acute_rows,
            "min_chronic_rows": min_chronic_rows,
            "chronic_days": chronic_days,
        }
    )
    
    rows = result.fetchall()
    series = []
    flags = []
    
    for row in rows:
        point_date = row[0]
        srpe_val = float(row[1])
        acute_val = float(row[2]) if row[2] is not None else None
        chronic_val = float(row[3]) if row[3] is not None else None
        acwr_val = float(row[4]) if row[4] is not None else None
        
        series.append(TrainingLoadPoint(
            date=point_date,
            srpe=srpe_val,
            acute=acute_val,
            chronic=chronic_val,
            acwr=acwr_val,
        ))
        
        # Generate flags
        if acwr_val is not None:
            if acwr_val > 1.5:
                flags.append({
                    "date": point_date.isoformat(),
                    "risk": "high",
                    "reason": f"acwr>{acwr_val:.2f}"
                })
            elif acwr_val < 0.8:
                flags.append({
                    "date": point_date.isoformat(),
                    "risk": "low",
                    "reason": f"acwr<{acwr_val:.2f}"
                })
    
    return TrainingLoadResponse(
        series=series,
        acute_days=acute_days,
        chronic_days=chronic_days,
        flags=flags,
    )


@router.get("/players/{player_id}/overview", response_model=PlayerOverviewResponse)
async def get_player_overview(
    player_id: UUID,
    period: Literal["7d", "28d", "30d", "90d"] = Query("28d", alias="period"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player overview with KPIs and data completeness.
    
    Returns:
    - Data completeness percentages
    - Last available metric values
    - Training session counts
    - Average sRPE for 7d and 28d
    """
    # Map period to days
    period_map = {"7d": 7, "28d": 28, "30d": 30, "90d": 90}
    window_days = period_map.get(period, 28)
    date_from = date.today() - timedelta(days=window_days)
    
    # Wellness days with data
    wellness_query = text("""
        SELECT COUNT(DISTINCT date)::int
        FROM wellness_sessions
        WHERE player_id = :player_id
          AND date >= :date_from
    """)
    wellness_result = await session.execute(
        wellness_query,
        {"player_id": player_id, "date_from": date_from}
    )
    wellness_days_with_data = wellness_result.scalar() or 0
    wellness_completeness_pct = round((wellness_days_with_data / window_days) * 100, 1) if window_days > 0 else 0
    
    # Last wellness values
    last_values_query = text("""
        SELECT
            wm.metric_key,
            wm.metric_value
        FROM wellness_sessions ws
        JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND ws.date = (
              SELECT MAX(date)
              FROM wellness_sessions
              WHERE player_id = :player_id
                AND date >= :date_from
          )
          AND wm.validity = 'valid'
    """)
    last_values_result = await session.execute(
        last_values_query,
        {"player_id": player_id, "date_from": date_from}
    )
    last_values = {
        row[0]: float(row[1]) for row in last_values_result.fetchall()
    }
    
    # Ensure all default metrics are in last_values (with None if missing)
    for metric in DEFAULT_WELLNESS_METRICS:
        if metric not in last_values:
            last_values[metric] = None
    
    # Training sessions count
    training_query = text("""
        SELECT
            COUNT(DISTINCT ta.training_session_id)::int AS total_sessions,
            COUNT(DISTINCT CASE WHEN ta.status = 'present' THEN ta.training_session_id END)::int AS present_count
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date >= :date_from
    """)
    training_result = await session.execute(
        training_query,
        {"player_id": player_id, "date_from": date_from}
    )
    training_row = training_result.fetchone()
    training_sessions = training_row[0] if training_row else 0
    present_count = training_row[1] if training_row else 0
    
    # Average sRPE last 7d
    srpe_7d_query = text("""
        SELECT AVG(daily_srpe)
        FROM (
            SELECT
                ts.session_date::date AS date,
                COALESCE(SUM(ta.rpe_post * ta.minutes), 0) AS daily_srpe
            FROM training_attendance ta
            JOIN training_sessions ts ON ts.id = ta.training_session_id
            WHERE ta.player_id = :player_id
              AND ts.session_date::date >= :date_from_7d
              AND ta.status = 'present'
              AND ta.rpe_post IS NOT NULL
              AND ta.minutes IS NOT NULL
            GROUP BY ts.session_date::date
        ) daily
    """)
    date_from_7d = date.today() - timedelta(days=7)
    srpe_7d_result = await session.execute(
        srpe_7d_query,
        {"player_id": player_id, "date_from_7d": date_from_7d}
    )
    avg_srpe_last_7d = float(srpe_7d_result.scalar() or 0)
    
    # Average sRPE last 28d
    srpe_28d_query = text("""
        SELECT AVG(daily_srpe)
        FROM (
            SELECT
                ts.session_date::date AS date,
                COALESCE(SUM(ta.rpe_post * ta.minutes), 0) AS daily_srpe
            FROM training_attendance ta
            JOIN training_sessions ts ON ts.id = ta.training_session_id
            WHERE ta.player_id = :player_id
              AND ts.session_date::date >= :date_from
              AND ta.status = 'present'
              AND ta.rpe_post IS NOT NULL
              AND ta.minutes IS NOT NULL
            GROUP BY ts.session_date::date
        ) daily
    """)
    srpe_28d_result = await session.execute(
        srpe_28d_query,
        {"player_id": player_id, "date_from": date_from}
    )
    avg_srpe_last_28d = float(srpe_28d_result.scalar() or 0)
    
    return PlayerOverviewResponse(
        window_days=window_days,
        wellness_days_with_data=wellness_days_with_data,
        wellness_completeness_pct=wellness_completeness_pct,
        last_values=last_values,
        training_sessions=training_sessions,
        present_count=present_count,
        avg_srpe_last_7d=avg_srpe_last_7d if avg_srpe_last_7d > 0 else None,
        avg_srpe_last_28d=avg_srpe_last_28d if avg_srpe_last_28d > 0 else None,
    )


@router.get("/players/{player_id}/training-metrics", response_model=ProgressResponse)
async def get_training_metrics(
    player_id: UUID,
    bucket: Literal["daily", "weekly", "monthly"] = Query("weekly"),
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    metrics: Optional[str] = Query(None, description="Comma-separated training metric keys"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get training metrics aggregated by time bucket.
    
    Returns training metrics (HSR, distance, sprints, HR, etc.) with delta vs previous bucket.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Parse metrics or use defaults
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = DEFAULT_TRAINING_METRICS
    
    # Map bucket to SQL date_trunc
    bucket_map = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month"
    }
    bucket_sql = bucket_map[bucket]
    
    # Build dynamic query for selected metrics
    metric_cases = []
    for metric in metric_list:
        metric_cases.append(
            f"AVG(CASE WHEN tm.metric_key = '{metric}' THEN tm.metric_value END) AS {metric}"
        )
    
    metrics_select = ",\n            ".join(metric_cases)
    
    # Query training metrics by bucket
    training_query = text(f"""
        WITH training_buckets AS (
            SELECT
                DATE_TRUNC(:bucket_sql, ts.session_date::timestamp)::date AS bucket_start,
                {metrics_select}
            FROM training_attendance ta
            JOIN training_sessions ts ON ts.id = ta.training_session_id
            LEFT JOIN training_metrics tm ON tm.training_attendance_id = ta.id
            WHERE ta.player_id = :player_id
              AND ts.session_date::date BETWEEN :date_from AND :date_to
              AND ta.status = 'present'
              AND (tm.metric_key = ANY(:metric_list) OR tm.metric_key IS NULL)
              AND (tm.validity = 'valid' OR tm.validity IS NULL)
            GROUP BY bucket_start
        )
        SELECT * FROM training_buckets
        ORDER BY bucket_start ASC
    """)
    
    training_result = await session.execute(
        training_query,
        {
            "bucket_sql": bucket_sql,
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "metric_list": metric_list,
        }
    )
    training_rows = training_result.fetchall()
    
    # Combine data and calculate deltas
    series = []
    prev_bucket_data = None
    
    for row in training_rows:
        bucket_start = row[0]
        bucket_data = {"bucket_start": bucket_start}
        
        # Add training metrics (columns 1+)
        for i, metric in enumerate(metric_list, start=1):
            bucket_data[metric] = float(row[i]) if row[i] is not None else None
        
        # Calculate delta vs previous bucket
        delta_prev_pct = {}
        if prev_bucket_data:
            for metric in metric_list:
                curr_val = bucket_data.get(metric)
                prev_val = prev_bucket_data.get(metric)
                if curr_val is not None and prev_val is not None and prev_val != 0:
                    delta_pct = ((curr_val - prev_val) / prev_val) * 100
                    delta_prev_pct[metric] = round(delta_pct, 2)
        
        bucket_data["delta_prev_pct"] = delta_prev_pct if delta_prev_pct else None
        series.append(ProgressSeriesPoint(**bucket_data))
        prev_bucket_data = bucket_data
    
    return ProgressResponse(
        bucket=bucket,
        date_from=date_from,
        date_to=date_to,
        series=series,
    )


@router.get("/players/{player_id}/match-metrics", response_model=ProgressResponse)
async def get_match_metrics(
    player_id: UUID,
    bucket: Literal["daily", "weekly", "monthly"] = Query("weekly"),
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    metrics: Optional[str] = Query(None, description="Comma-separated match metric keys"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get match performance metrics aggregated by time bucket.
    
    Returns match metrics (pass accuracy, duels, touches, etc.) with delta vs previous bucket.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Parse metrics or use defaults
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = DEFAULT_MATCH_METRICS
    
    # Map bucket to SQL date_trunc
    bucket_map = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month"
    }
    bucket_sql = bucket_map[bucket]
    
    # Build dynamic query for selected metrics
    metric_cases = []
    for metric in metric_list:
        metric_cases.append(
            f"AVG(CASE WHEN mm.metric_key = '{metric}' THEN mm.metric_value END) AS {metric}"
        )
    
    metrics_select = ",\n            ".join(metric_cases)
    
    # Query match metrics by bucket
    match_query = text(f"""
        WITH match_buckets AS (
            SELECT
                DATE_TRUNC(:bucket_sql, m.match_date::timestamp)::date AS bucket_start,
                {metrics_select}
            FROM attendances a
            JOIN matches m ON m.id = a.match_id
            LEFT JOIN match_metrics mm ON mm.attendance_id = a.id
            WHERE a.player_id = :player_id
              AND m.match_date::date BETWEEN :date_from AND :date_to
              AND (mm.metric_key = ANY(:metric_list) OR mm.metric_key IS NULL)
              AND (mm.validity = 'valid' OR mm.validity IS NULL)
            GROUP BY bucket_start
        )
        SELECT * FROM match_buckets
        ORDER BY bucket_start ASC
    """)
    
    match_result = await session.execute(
        match_query,
        {
            "bucket_sql": bucket_sql,
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "metric_list": metric_list,
        }
    )
    match_rows = match_result.fetchall()
    
    # Combine data and calculate deltas
    series = []
    prev_bucket_data = None
    
    for row in match_rows:
        bucket_start = row[0]
        bucket_data = {"bucket_start": bucket_start}
        
        # Add match metrics (columns 1+)
        for i, metric in enumerate(metric_list, start=1):
            bucket_data[metric] = float(row[i]) if row[i] is not None else None
        
        # Calculate delta vs previous bucket
        delta_prev_pct = {}
        if prev_bucket_data:
            for metric in metric_list:
                curr_val = bucket_data.get(metric)
                prev_val = prev_bucket_data.get(metric)
                if curr_val is not None and prev_val is not None and prev_val != 0:
                    delta_pct = ((curr_val - prev_val) / prev_val) * 100
                    delta_prev_pct[metric] = round(delta_pct, 2)
        
        bucket_data["delta_prev_pct"] = delta_prev_pct if delta_prev_pct else None
        series.append(ProgressSeriesPoint(**bucket_data))
        prev_bucket_data = bucket_data
    
    return ProgressResponse(
        bucket=bucket,
        date_from=date_from,
        date_to=date_to,
        series=series,
    )

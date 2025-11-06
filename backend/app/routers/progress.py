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
from app.analytics.training_load import (
    calculate_acwr_rolling,
    calculate_monotony_weekly,
    calculate_strain_weekly,
)
from app.analytics.readiness import (
    calculate_readiness_index,
    calculate_baseline_28d,
)
from app.analytics.alerts import generate_alerts

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
    srpe: float  # Raw daily sRPE
    acute: Optional[float] = None
    chronic: Optional[float] = None
    acwr: Optional[float] = None


class TrainingLoadResponse(BaseModel):
    """Response for training-load endpoint."""
    series: list[TrainingLoadPoint]
    window_short: int
    window_long: int
    acwr_latest: Optional[float] = None
    acwr_series: list[dict] = []
    monotony_weekly: list[dict] = []
    strain_weekly: list[dict] = []
    flags: list[dict] = []


class FamilyCompleteness(BaseModel):
    """Completeness data for a metric family."""
    family: str
    completeness_pct: float
    days_with_data: int
    total_days: int


class PlayerOverviewResponse(BaseModel):
    """Response for overview endpoint."""
    player_id: UUID
    period_days: int
    wellness_entries: int
    training_sessions: int
    matches: int
    wellness_completeness_pct: float
    training_completeness_pct: float
    match_completeness_pct: float
    family_completeness: list[FamilyCompleteness]
    metric_summaries: list[dict]
    data_quality_issues: int = 0


@router.get("/players/{player_id}/progress", response_model=ProgressResponse)
async def get_player_progress(
    player_id: UUID,
    grouping: Literal["day", "week", "month"] = Query("week", alias="grouping"),
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    families: Optional[str] = Query(None, description="Comma-separated family names (wellness, training, match, tactical)"),
    metrics: Optional[str] = Query(None, description="Comma-separated metric keys"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player progress metrics aggregated by time bucket.
    
    Returns EAV metrics grouped by time period with flexible family filtering.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Map grouping to SQL date_trunc and bucket name
    grouping_map = {
        "day": ("day", "daily"),
        "week": ("week", "weekly"),
        "month": ("month", "monthly")
    }
    bucket_sql, bucket_name = grouping_map.get(grouping, ("week", "weekly"))
    
    # Determine which families to query
    if families:
        family_list = [f.strip().lower() for f in families.split(",")]
    else:
        family_list = ["wellness", "training", "match", "tactical"]
    
    # Parse metrics or use defaults based on families
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = []
        if "wellness" in family_list:
            metric_list.extend(DEFAULT_WELLNESS_METRICS)
        if "training" in family_list:
            metric_list.extend(DEFAULT_TRAINING_METRICS)
        if "match" in family_list:
            metric_list.extend(DEFAULT_MATCH_METRICS)
        if "tactical" in family_list:
            metric_list.extend(["pressures", "recoveries_def_third", "progressive_passes", "line_breaking_passes_conceded", "xthreat_contrib"])
    
    # Build UNION query for all EAV sources
    all_queries = []
    
    # Wellness metrics
    if "wellness" in family_list:
        wellness_metrics = [m for m in metric_list if m in DEFAULT_WELLNESS_METRICS]
        if wellness_metrics:
            metric_cases = []
            for metric in metric_list:
                metric_cases.append(
                    f"AVG(CASE WHEN metric_key = '{metric}' THEN metric_value END) AS {metric}"
                )
            metrics_select = ",\n                ".join(metric_cases)
            all_queries.append(f"""
                SELECT
                    DATE_TRUNC('{bucket_sql}', date::timestamp)::date AS bucket_start,
                    {metrics_select}
                FROM (
                    SELECT ws.date, wm.metric_key, wm.metric_value
                    FROM wellness_sessions ws
                    JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
                    WHERE ws.player_id = :player_id
                      AND ws.date BETWEEN :date_from AND :date_to
                      AND wm.metric_key = ANY(:metric_list)
                      AND wm.validity = 'valid'
                ) wellness_data
                GROUP BY bucket_start
            """)
    
    # Training metrics
    if "training" in family_list:
        training_metrics = [m for m in metric_list if m in DEFAULT_TRAINING_METRICS]
        if training_metrics:
            metric_cases = []
            for metric in metric_list:
                metric_cases.append(
                    f"AVG(CASE WHEN metric_key = '{metric}' THEN metric_value END) AS {metric}"
                )
            metrics_select = ",\n                ".join(metric_cases)
            all_queries.append(f"""
                SELECT
                    DATE_TRUNC('{bucket_sql}', session_date::timestamp)::date AS bucket_start,
                    {metrics_select}
                FROM (
                    SELECT ts.session_date::date AS session_date, tm.metric_key, tm.metric_value
                    FROM training_attendance ta
                    JOIN training_sessions ts ON ts.id = ta.training_session_id
                    LEFT JOIN training_metrics tm ON tm.training_attendance_id = ta.id
                    WHERE ta.player_id = :player_id
                      AND ts.session_date::date BETWEEN :date_from AND :date_to
                      AND ta.status = 'present'
                      AND (tm.metric_key = ANY(:metric_list) OR tm.metric_key IS NULL)
                      AND (tm.validity = 'valid' OR tm.validity IS NULL)
                ) training_data
                GROUP BY bucket_start
            """)
    
    # Match metrics
    if "match" in family_list or "tactical" in family_list:
        match_metrics = [m for m in metric_list if m in DEFAULT_MATCH_METRICS or m.startswith(('pressures', 'recoveries', 'progressive', 'line_breaking', 'xthreat'))]
        if match_metrics:
            metric_cases = []
            for metric in metric_list:
                metric_cases.append(
                    f"AVG(CASE WHEN metric_key = '{metric}' THEN metric_value END) AS {metric}"
                )
            metrics_select = ",\n                ".join(metric_cases)
            all_queries.append(f"""
                SELECT
                    DATE_TRUNC('{bucket_sql}', match_date::timestamp)::date AS bucket_start,
                    {metrics_select}
                FROM (
                    SELECT m.match_date::date AS match_date, mm.metric_key, mm.metric_value
                    FROM attendances a
                    JOIN matches m ON m.id = a.match_id
                    LEFT JOIN match_metrics mm ON mm.attendance_id = a.id
                    WHERE a.player_id = :player_id
                      AND m.match_date::date BETWEEN :date_from AND :date_to
                      AND (mm.metric_key = ANY(:metric_list) OR mm.metric_key IS NULL)
                      AND (mm.validity = 'valid' OR mm.validity IS NULL)
                ) match_data
                GROUP BY bucket_start
            """)
    
    # Combine all queries with UNION ALL and aggregate
    if not all_queries:
        # No families selected, return empty
        return ProgressResponse(
            bucket=bucket_name,
            date_from=date_from,
            date_to=date_to,
            series=[],
        )
    
    combined_query = f"""
        WITH all_metrics AS (
            {' UNION ALL '.join(all_queries)}
        )
        SELECT
            bucket_start,
            {', '.join([f'AVG({m}) AS {m}' for m in metric_list])}
        FROM all_metrics
        GROUP BY bucket_start
        ORDER BY bucket_start ASC
    """
    
    result = await session.execute(
        text(combined_query),
        {
            "player_id": player_id,
            "date_from": date_from,
            "date_to": date_to,
            "metric_list": metric_list,
        }
    )
    rows = result.fetchall()
    
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
    
    # Combine metrics and sRPE data, calculate deltas
    series = []
    prev_bucket_data = None
    
    for row in rows:
        bucket_start = row[0]
        bucket_data = {
            "bucket_start": bucket_start,
            "srpe": srpe_rows.get(bucket_start),
        }
        
        # Add metrics (columns 1+)
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
    window_short: int = Query(7, ge=1, le=14, description="Short window for acute load (days)"),
    window_long: int = Query(28, ge=7, le=56, description="Long window for chronic load (days)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get training load with ACWR (Acute:Chronic Workload Ratio).
    
    - sRPE = RPE * minutes per day (raw daily values returned)
    - acute = rolling average of last window_short days
    - chronic = rolling average of last window_long days
    - ACWR = acute / chronic
    - Flags: high if ACWR > 1.5, low if ACWR < 0.8
    """
    # Get daily sRPE for last window_long + buffer
    date_from = date.today() - timedelta(days=window_long + 7)
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
    
    acute_rows = window_short - 1  # ROWS BETWEEN is inclusive
    chronic_rows = window_long - 1
    min_acute_rows = max(window_short - 2, 1)  # Allow some missing days
    min_chronic_rows = max(window_long - 5, 1)
    
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
            "chronic_days": window_long,
        }
    )
    
    rows = result.fetchall()
    series = []
    flags = []
    
    # Build daily_srpe list for analytics calculations
    daily_srpe_list = []
    for row in rows:
        point_date = row[0]
        srpe_val = float(row[1])
        daily_srpe_list.append((point_date, srpe_val))
        
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
    
    # Calculate Monotony and Strain
    monotony_weekly = calculate_monotony_weekly(daily_srpe_list)
    strain_weekly = calculate_strain_weekly(daily_srpe_list, monotony_weekly)
    
    # Get latest ACWR
    acwr_latest = None
    if series:
        latest_point = series[-1]
        acwr_latest = latest_point.acwr
    
    # Format series for response
    acwr_series_formatted = [
        {"date": d.isoformat(), "value": acwr}
        for d, acwr in calculate_acwr_rolling(daily_srpe_list, window_short, window_long)
        if acwr is not None
    ]
    monotony_formatted = [
        {"week_start": d.isoformat(), "value": m}
        for d, m in monotony_weekly
        if m is not None
    ]
    strain_formatted = [
        {"week_start": d.isoformat(), "value": s}
        for d, s in strain_weekly
        if s is not None
    ]
    
    return TrainingLoadResponse(
        series=series,
        window_short=window_short,
        window_long=window_long,
        acwr_latest=acwr_latest,
        acwr_series=acwr_series_formatted,
        monotony_weekly=monotony_formatted,
        strain_weekly=strain_formatted,
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
    
    # Calculate completeness per family
    family_completeness = []
    
    # Wellness completeness
    family_completeness.append(FamilyCompleteness(
        family="wellness",
        completeness_pct=wellness_completeness_pct,
        days_with_data=wellness_days_with_data,
        total_days=window_days,
    ))
    
    # Training completeness
    training_completeness_pct = round((training_sessions / max(window_days // 3, 1)) * 100, 1) if window_days > 0 else 0  # Approx 3 sessions per week
    family_completeness.append(FamilyCompleteness(
        family="training",
        completeness_pct=min(training_completeness_pct, 100.0),
        days_with_data=training_sessions,
        total_days=window_days,
    ))
    
    # Match completeness
    match_query = text("""
        SELECT COUNT(DISTINCT m.id)::int
        FROM attendances a
        JOIN matches m ON m.id = a.match_id
        WHERE a.player_id = :player_id
          AND m.match_date::date >= :date_from
    """)
    match_result = await session.execute(
        match_query,
        {"player_id": player_id, "date_from": date_from}
    )
    matches = match_result.scalar() or 0
    match_completeness_pct = round((matches / max(window_days // 7, 1)) * 100, 1) if window_days > 0 else 0  # Approx 1 match per week
    family_completeness.append(FamilyCompleteness(
        family="match",
        completeness_pct=min(match_completeness_pct, 100.0),
        days_with_data=matches,
        total_days=window_days,
    ))
    
    # Metric summaries (last values with basic stats)
    metric_summaries = []
    for metric_key, metric_value in last_values.items():
        if metric_value is not None:
            # Get avg, min, max for this metric in the period
            stats_query = text("""
                SELECT
                    AVG(metric_value) AS avg_val,
                    MIN(metric_value) AS min_val,
                    MAX(metric_value) AS max_val,
                    COUNT(*) AS count
                FROM wellness_metrics wm
                JOIN wellness_sessions ws ON ws.id = wm.wellness_session_id
                WHERE ws.player_id = :player_id
                  AND ws.date >= :date_from
                  AND wm.metric_key = :metric_key
                  AND wm.validity = 'valid'
            """)
            stats_result = await session.execute(
                stats_query,
                {"player_id": player_id, "date_from": date_from, "metric_key": metric_key}
            )
            stats_row = stats_result.fetchone()
            if stats_row and stats_row[3] > 0:  # count > 0
                metric_summaries.append({
                    "metric_key": metric_key,
                    "current_value": metric_value,
                    "avg_value": round(float(stats_row[0]), 2),
                    "min_value": round(float(stats_row[1]), 2),
                    "max_value": round(float(stats_row[2]), 2),
                    "completeness_pct": round((stats_row[3] / window_days) * 100, 1),
                    "trend_pct": 0.0,  # Placeholder
                    "variance": round(float(stats_row[2]) - float(stats_row[1]), 2) if stats_row[2] and stats_row[1] else 0.0,
                })
    
    # Data quality issues count (placeholder)
    data_quality_issues = 0
    
    return PlayerOverviewResponse(
        player_id=player_id,
        period_days=window_days,
        wellness_entries=wellness_days_with_data,
        training_sessions=training_sessions,
        matches=matches,
        wellness_completeness_pct=wellness_completeness_pct,
        training_completeness_pct=min(training_completeness_pct, 100.0),
        match_completeness_pct=min(match_completeness_pct, 100.0),
        family_completeness=family_completeness,
        metric_summaries=metric_summaries,
        data_quality_issues=data_quality_issues,
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
    
    Alias for /progress with families=training.
    Returns training metrics (HSR, distance, sprints, HR, etc.) with delta vs previous bucket.
    """
    # Redirect to progress endpoint with families=training
    return await get_player_progress(
        player_id=player_id,
        grouping="week" if bucket == "weekly" else ("day" if bucket == "daily" else "month"),
        date_from=date_from,
        date_to=date_to,
        families="training",
        metrics=metrics,
        session=session,
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
    
    Alias for /progress with families=match,tactical.
    Returns match metrics (pass accuracy, duels, touches, etc.) with delta vs previous bucket.
    """
    # Redirect to progress endpoint with families=match,tactical
    return await get_player_progress(
        player_id=player_id,
        grouping="week" if bucket == "weekly" else ("day" if bucket == "daily" else "month"),
        date_from=date_from,
        date_to=date_to,
        families="match,tactical",
        metrics=metrics,
        session=session,
    )


class MatchSummaryPoint(BaseModel):
    """Single match summary point."""
    match_id: UUID
    match_date: date
    opponent: str
    is_home: bool
    minutes_played: int
    # Match metrics
    pass_accuracy: Optional[float] = None
    passes_completed: Optional[int] = None
    duels_won: Optional[int] = None
    touches: Optional[int] = None
    dribbles_success: Optional[int] = None
    interceptions: Optional[int] = None
    tackles: Optional[int] = None
    shots_on_target: Optional[int] = None
    # Tactical metrics
    pressures: Optional[int] = None
    recoveries_def_third: Optional[int] = None
    progressive_passes: Optional[int] = None
    line_breaking_passes_conceded: Optional[int] = None
    xthreat_contrib: Optional[float] = None


class MatchSummaryResponse(BaseModel):
    """Response for match-summary endpoint."""
    player_id: UUID
    date_from: date
    date_to: date
    matches: list[MatchSummaryPoint]
    aggregates: dict


@router.get("/players/{player_id}/match-summary", response_model=MatchSummaryResponse)
async def get_match_summary(
    player_id: UUID,
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get match summary with aggregated match and tactical metrics.
    
    Returns per-match statistics and period aggregates.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Query matches with metrics
    query = text("""
        SELECT
            m.id AS match_id,
            m.match_date::date AS match_date,
            m.opponent_name AS opponent,
            m.is_home,
            a.minutes_played,
            -- Match metrics
            AVG(CASE WHEN mm.metric_key = 'pass_accuracy' THEN mm.metric_value END) AS pass_accuracy,
            SUM(CASE WHEN mm.metric_key = 'passes_completed' THEN mm.metric_value::int END) AS passes_completed,
            SUM(CASE WHEN mm.metric_key = 'duels_won' THEN mm.metric_value::int END) AS duels_won,
            SUM(CASE WHEN mm.metric_key = 'touches' THEN mm.metric_value::int END) AS touches,
            SUM(CASE WHEN mm.metric_key = 'dribbles_success' THEN mm.metric_value::int END) AS dribbles_success,
            SUM(CASE WHEN mm.metric_key = 'interceptions' THEN mm.metric_value::int END) AS interceptions,
            SUM(CASE WHEN mm.metric_key = 'tackles' THEN mm.metric_value::int END) AS tackles,
            SUM(CASE WHEN mm.metric_key = 'shots_on_target' THEN mm.metric_value::int END) AS shots_on_target,
            -- Tactical metrics
            SUM(CASE WHEN mm.metric_key = 'pressures' THEN mm.metric_value::int END) AS pressures,
            SUM(CASE WHEN mm.metric_key = 'recoveries_def_third' THEN mm.metric_value::int END) AS recoveries_def_third,
            SUM(CASE WHEN mm.metric_key = 'progressive_passes' THEN mm.metric_value::int END) AS progressive_passes,
            SUM(CASE WHEN mm.metric_key = 'line_breaking_passes_conceded' THEN mm.metric_value::int END) AS line_breaking_passes_conceded,
            AVG(CASE WHEN mm.metric_key = 'xthreat_contrib' THEN mm.metric_value END) AS xthreat_contrib
        FROM attendances a
        JOIN matches m ON m.id = a.match_id
        LEFT JOIN match_metrics mm ON mm.attendance_id = a.id
        WHERE a.player_id = :player_id
          AND m.match_date::date BETWEEN :date_from AND :date_to
          AND (mm.validity = 'valid' OR mm.validity IS NULL)
        GROUP BY m.id, m.match_date, m.opponent_name, m.is_home, a.minutes_played
        ORDER BY m.match_date ASC
    """)
    
    result = await session.execute(
        query,
        {"player_id": player_id, "date_from": date_from, "date_to": date_to}
    )
    rows = result.fetchall()
    
    matches = []
    for row in rows:
        matches.append(MatchSummaryPoint(
            match_id=row[0],
            match_date=row[1],
            opponent=row[2] or "Unknown",
            is_home=row[3] if row[3] is not None else False,
            minutes_played=int(row[4]) if row[4] else 0,
            pass_accuracy=float(row[5]) if row[5] is not None else None,
            passes_completed=int(row[6]) if row[6] is not None else None,
            duels_won=int(row[7]) if row[7] is not None else None,
            touches=int(row[8]) if row[8] is not None else None,
            dribbles_success=int(row[9]) if row[9] is not None else None,
            interceptions=int(row[10]) if row[10] is not None else None,
            tackles=int(row[11]) if row[11] is not None else None,
            shots_on_target=int(row[12]) if row[12] is not None else None,
            pressures=int(row[13]) if row[13] is not None else None,
            recoveries_def_third=int(row[14]) if row[14] is not None else None,
            progressive_passes=int(row[15]) if row[15] is not None else None,
            line_breaking_passes_conceded=int(row[16]) if row[16] is not None else None,
            xthreat_contrib=float(row[17]) if row[17] is not None else None,
        ))
    
    # Calculate aggregates
    if matches:
        aggregates = {
            "total_matches": len(matches),
            "avg_minutes": round(sum(m.minutes_played for m in matches) / len(matches), 1),
            "avg_pass_accuracy": round(sum(m.pass_accuracy for m in matches if m.pass_accuracy) / len([m for m in matches if m.pass_accuracy]), 1) if any(m.pass_accuracy for m in matches) else None,
            "total_passes": sum(m.passes_completed for m in matches if m.passes_completed),
            "total_duels_won": sum(m.duels_won for m in matches if m.duels_won),
            "total_touches": sum(m.touches for m in matches if m.touches),
        }
    else:
        aggregates = {}
    
    return MatchSummaryResponse(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        matches=matches,
        aggregates=aggregates,
    )


class ReadinessPoint(BaseModel):
    """Single readiness data point."""
    date: date
    readiness: Optional[float]  # 0-100


class ReadinessResponse(BaseModel):
    """Response for readiness endpoint."""
    player_id: UUID
    date_from: date
    date_to: date
    series: list[ReadinessPoint]
    latest_value: Optional[float] = None
    avg_7d: Optional[float] = None


@router.get("/players/{player_id}/readiness", response_model=ReadinessResponse)
async def get_player_readiness(
    player_id: UUID,
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get player readiness index (0-100) based on z-scores of wellness metrics.
    
    Uses 28-day rolling baseline for normalization.
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Extend date_from to get 28-day baseline
    baseline_start = date_from - timedelta(days=28)
    
    # Fetch wellness data
    wellness_query = text("""
        SELECT
            ws.date,
            MAX(CASE WHEN wm.metric_key = 'hrv_ms' THEN wm.metric_value END) AS hrv_ms,
            MAX(CASE WHEN wm.metric_key = 'resting_hr_bpm' THEN wm.metric_value END) AS resting_hr_bpm,
            MAX(CASE WHEN wm.metric_key = 'sleep_quality' THEN wm.metric_value END) AS sleep_quality,
            MAX(CASE WHEN wm.metric_key = 'soreness' THEN wm.metric_value END) AS soreness,
            MAX(CASE WHEN wm.metric_key = 'stress' THEN wm.metric_value END) AS stress,
            MAX(CASE WHEN wm.metric_key = 'mood' THEN wm.metric_value END) AS mood,
            MAX(CASE WHEN wm.metric_key = 'body_weight_kg' THEN wm.metric_value END) AS body_weight_kg
        FROM wellness_sessions ws
        LEFT JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND ws.date BETWEEN :baseline_start AND :date_to
          AND wm.validity = 'valid'
        GROUP BY ws.date
        ORDER BY ws.date ASC
    """)
    
    result = await session.execute(
        wellness_query,
        {
            "player_id": player_id,
            "baseline_start": baseline_start,
            "date_to": date_to,
        }
    )
    rows = result.fetchall()
    
    # Build wellness data list
    wellness_data = []
    for row in rows:
        d = row[0]
        metrics = {
            'hrv_ms': float(row[1]) if row[1] is not None else None,
            'resting_hr_bpm': float(row[2]) if row[2] is not None else None,
            'sleep_quality': float(row[3]) if row[3] is not None else None,
            'soreness': float(row[4]) if row[4] is not None else None,
            'stress': float(row[5]) if row[5] is not None else None,
            'mood': float(row[6]) if row[6] is not None else None,
            'body_weight_kg': float(row[7]) if row[7] is not None else None,
        }
        wellness_data.append((d, metrics))
    
    # Calculate readiness for each day
    readiness_series = []
    for d, metrics in wellness_data:
        if d < date_from:
            continue  # Skip baseline days
        
        # Calculate baseline up to this date
        baseline = calculate_baseline_28d(wellness_data, d)
        
        # Calculate readiness
        readiness = calculate_readiness_index(
            metrics['hrv_ms'],
            metrics['resting_hr_bpm'],
            metrics['sleep_quality'],
            metrics['soreness'],
            metrics['stress'],
            metrics['mood'],
            metrics['body_weight_kg'],
            baseline
        )
        
        readiness_series.append(ReadinessPoint(date=d, readiness=readiness))
    
    # Get latest value and 7d average
    latest_value = None
    avg_7d = None
    
    if readiness_series:
        latest_value = readiness_series[-1].readiness
        
        # Calculate 7d average
        last_7d = [r.readiness for r in readiness_series[-7:] if r.readiness is not None]
        if last_7d:
            avg_7d = sum(last_7d) / len(last_7d)
    
    return ReadinessResponse(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        series=readiness_series,
        latest_value=latest_value,
        avg_7d=avg_7d,
    )


class AlertResponse(BaseModel):
    """Single alert response."""
    type: str
    metric: str
    date: str
    value: float
    threshold: str
    severity: str


class AlertsResponse(BaseModel):
    """Response for alerts endpoint."""
    player_id: UUID
    date_from: date
    date_to: date
    alerts: list[AlertResponse]


@router.get("/players/{player_id}/alerts", response_model=AlertsResponse)
async def get_player_alerts(
    player_id: UUID,
    date_from: Optional[date] = Query(None, alias="date_from"),
    date_to: Optional[date] = Query(None, alias="date_to"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get alerts for a player based on ACWR, Readiness, and outlier detection.
    
    Alert types:
    - risk_load: ACWR outside [0.8, 1.5]
    - risk_fatigue: Readiness < 40 for 3+ consecutive days
    - risk_outlier: |z-score| >= 2 for resting_hr_bpm, hrv_ms, soreness, mood
    """
    # Default date range: last 90 days
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Get training load data for ACWR (extend back 35 days for baseline)
    load_date_from = date_from - timedelta(days=35)
    load_query = text("""
        SELECT
            ts.session_date::date AS date,
            COALESCE(SUM(ta.rpe_post * ta.minutes), 0) AS srpe
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date BETWEEN :load_date_from AND :date_to
          AND ta.status = 'present'
          AND ta.rpe_post IS NOT NULL
          AND ta.minutes IS NOT NULL
        GROUP BY ts.session_date::date
        ORDER BY ts.session_date::date ASC
    """)
    
    load_result = await session.execute(
        load_query,
        {"player_id": player_id, "load_date_from": load_date_from, "date_to": date_to}
    )
    daily_srpe = [(row[0], float(row[1])) for row in load_result.fetchall()]
    
    # Calculate ACWR series
    acwr_series = calculate_acwr_rolling(daily_srpe, 7, 28)
    
    # Get readiness data
    readiness_endpoint = await get_player_readiness(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        session=session,
    )
    readiness_series = [(r.date, r.readiness) for r in readiness_endpoint.series]
    
    # Get wellness data for outlier detection (extend back 28 days for baseline)
    wellness_date_from = date_from - timedelta(days=28)
    wellness_query = text("""
        SELECT
            ws.date,
            MAX(CASE WHEN wm.metric_key = 'resting_hr_bpm' THEN wm.metric_value END) AS resting_hr_bpm,
            MAX(CASE WHEN wm.metric_key = 'hrv_ms' THEN wm.metric_value END) AS hrv_ms,
            MAX(CASE WHEN wm.metric_key = 'soreness' THEN wm.metric_value END) AS soreness,
            MAX(CASE WHEN wm.metric_key = 'mood' THEN wm.metric_value END) AS mood
        FROM wellness_sessions ws
        LEFT JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND ws.date BETWEEN :wellness_date_from AND :date_to
          AND wm.validity = 'valid'
        GROUP BY ws.date
        ORDER BY ws.date ASC
    """)
    
    wellness_result = await session.execute(
        wellness_query,
        {
            "player_id": player_id,
            "wellness_date_from": wellness_date_from,
            "date_to": date_to,
        }
    )
    wellness_data = []
    for row in wellness_result.fetchall():
        d = row[0]
        metrics = {
            'resting_hr_bpm': float(row[1]) if row[1] is not None else None,
            'hrv_ms': float(row[2]) if row[2] is not None else None,
            'soreness': float(row[3]) if row[3] is not None else None,
            'mood': float(row[4]) if row[4] is not None else None,
        }
        wellness_data.append((d, metrics))
    
    # Calculate baseline for outlier detection
    baseline = calculate_baseline_28d(wellness_data, date_to)
    
    # Generate alerts
    alerts = generate_alerts(
        acwr_series,
        readiness_series,
        wellness_data,
        baseline,
        date_from,
        date_to
    )
    
    # Format alerts
    alerts_formatted = [AlertResponse(**alert.to_dict()) for alert in alerts]
    
    return AlertsResponse(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        alerts=alerts_formatted,
    )

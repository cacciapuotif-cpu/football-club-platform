"""Players API router - CRUD operations."""

from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from datetime import date, timedelta
from sqlalchemy import text, func, and_

from app.database import get_session
from app.models.organization import Organization
from app.models.player import Player
from app.models.sensor import SensorData
from app.models.session import TrainingSession
from app.models.wellness_eav import WellnessSession, WellnessMetric
from app.models.training_eav import TrainingAttendance, TrainingMetric
from app.schemas.player import (
    PlayerCreate, PlayerResponse, PlayerUpdate,
    PlayerProfileResponse, PlayerProfileUpdate,
    WeightCreate, WeightPoint, WeightSeriesResponse,
    MetricsCreate, MetricsRow, MetricsResponse,
    ReportResponse, ReportKPI, ReportPoint
)
from app.schemas.session import TrainingSessionResponse

router = APIRouter()


async def get_demo_org_id(session: AsyncSession) -> UUID:
    """Get the first organization ID for demo purposes (no auth)."""
    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise HTTPException(status_code=404, detail="No organization found. Please run seed script.")
    return org_id


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new player."""
    # Get demo organization ID (no auth)
    org_id = await get_demo_org_id(session)
    # Create player with organization_id
    player = Player(**player_data.model_dump(), organization_id=org_id)
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.get("/", response_model=list[PlayerResponse])
async def list_players(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: UUID | None = Query(None, description="Filter by team ID"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: str | None = Query(None, description="Filter by primary role (GK, DF, MF, FW)"),
):
    """List all players for the demo organization with optional filters (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    query = select(Player).where(Player.organization_id == org_id)

    # Apply filters
    if team_id:
        query = query.where(Player.team_id == team_id)
    if is_active is not None:
        query = query.where(Player.is_active == is_active)
    if role:
        query = query.where(Player.role_primary == role.upper())

    query = query.offset(skip).limit(limit).order_by(Player.last_name, Player.first_name)

    result = await session.execute(query)
    players = result.scalars().all()
    return players


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific player by ID (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    return player


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: UUID,
    player_data: PlayerUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a player's information (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Update only provided fields
    update_data = player_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)

    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a player (soft delete by setting is_active=False) (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Soft delete
    player.is_active = False
    session.add(player)
    await session.commit()
    return None


@router.get("/{player_id}/sessions", response_model=list[TrainingSessionResponse])
async def get_player_sessions(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get all training sessions for a specific player (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    # First verify the player exists and belongs to the organization
    player_result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = player_result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Get all sessions where this player has sensor data
    query = (
        select(TrainingSession)
        .join(SensorData, SensorData.session_id == TrainingSession.id)
        .where(
            SensorData.player_id == player_id,
            TrainingSession.organization_id == org_id
        )
        .order_by(TrainingSession.session_date.desc())
    )

    result = await session.execute(query)
    sessions = result.scalars().all()
    return sessions


@router.get("/{player_id}/profile", response_model=PlayerProfileResponse)
async def get_player_profile(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get player profile with last weight."""
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get last weight from wellness_metrics
    weight_query = text("""
        SELECT wm.metric_value, ws.date
        FROM wellness_metrics wm
        JOIN wellness_sessions ws ON ws.id = wm.wellness_session_id
        WHERE ws.player_id = :player_id
          AND wm.metric_key = 'body_weight_kg'
        ORDER BY ws.date DESC
        LIMIT 1
    """)
    weight_result = await session.execute(weight_query, {"player_id": str(player_id)})
    weight_row = weight_result.fetchone()
    
    last_weight_kg = float(weight_row[0]) if weight_row and weight_row[0] else None
    last_weight_date = weight_row[1] if weight_row and weight_row[1] else None
    
    return PlayerProfileResponse(
        id=player.id,
        first_name=player.first_name,
        last_name=player.last_name,
        date_of_birth=player.date_of_birth,
        place_of_birth=player.place_of_birth,
        nationality=player.nationality,
        tax_code=player.tax_code,
        email=player.email,
        phone=player.phone,
        address=player.address,
        role_primary=player.role_primary,
        role_secondary=player.role_secondary,
        dominant_foot=player.dominant_foot,
        dominant_arm=player.dominant_arm,
        jersey_number=player.jersey_number,
        height_cm=player.height_cm,
        foto_url=player.foto_url,
        notes=player.notes,
        consent_given=player.consent_given,
        consent_date=player.consent_date,
        last_weight_kg=last_weight_kg,
        last_weight_date=last_weight_date,
    )


@router.put("/{player_id}/profile", response_model=PlayerProfileResponse)
async def update_player_profile(
    player_id: UUID,
    profile_data: PlayerProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update player profile."""
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)
    
    session.add(player)
    await session.commit()
    await session.refresh(player)
    
    # Get last weight
    weight_query = text("""
        SELECT wm.metric_value, ws.date
        FROM wellness_metrics wm
        JOIN wellness_sessions ws ON ws.id = wm.wellness_session_id
        WHERE ws.player_id = :player_id
          AND wm.metric_key = 'body_weight_kg'
        ORDER BY ws.date DESC
        LIMIT 1
    """)
    weight_result = await session.execute(weight_query, {"player_id": str(player_id)})
    weight_row = weight_result.fetchone()
    
    last_weight_kg = float(weight_row[0]) if weight_row and weight_row[0] else None
    last_weight_date = weight_row[1] if weight_row and weight_row[1] else None
    
    return PlayerProfileResponse(
        id=player.id,
        first_name=player.first_name,
        last_name=player.last_name,
        date_of_birth=player.date_of_birth,
        place_of_birth=player.place_of_birth,
        nationality=player.nationality,
        tax_code=player.tax_code,
        email=player.email,
        phone=player.phone,
        address=player.address,
        role_primary=player.role_primary,
        role_secondary=player.role_secondary,
        dominant_foot=player.dominant_foot,
        dominant_arm=player.dominant_arm,
        jersey_number=player.jersey_number,
        height_cm=player.height_cm,
        foto_url=player.foto_url,
        notes=player.notes,
        consent_given=player.consent_given,
        consent_date=player.consent_date,
        last_weight_kg=last_weight_kg,
        last_weight_date=last_weight_date,
    )


@router.post("/{player_id}/weight", response_model=WeightPoint, status_code=status.HTTP_201_CREATED)
async def add_player_weight(
    player_id: UUID,
    weight_data: WeightCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Add weight entry for a player."""
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get or create wellness session for this date
    ws_result = await session.execute(
        select(WellnessSession).where(
            WellnessSession.player_id == player_id,
            WellnessSession.date == weight_data.date
        )
    )
    ws = ws_result.scalar_one_or_none()
    
    if not ws:
        ws = WellnessSession(
            player_id=player_id,
            date=weight_data.date,
            source="manual",
            organization_id=org_id,
        )
        session.add(ws)
        await session.flush()
    
    # Check if weight metric already exists for this date
    metric_result = await session.execute(
        select(WellnessMetric).where(
            WellnessMetric.wellness_session_id == ws.id,
            WellnessMetric.metric_key == "body_weight_kg"
        )
    )
    metric = metric_result.scalar_one_or_none()
    
    if metric:
        # Update existing
        metric.metric_value = weight_data.weight_kg
    else:
        # Create new
        metric = WellnessMetric(
            wellness_session_id=ws.id,
            metric_key="body_weight_kg",
            metric_value=weight_data.weight_kg,
            unit="kg",
        )
        session.add(metric)
    
    await session.commit()
    return WeightPoint(date=weight_data.date, weight_kg=weight_data.weight_kg)


@router.get("/{player_id}/weights", response_model=WeightSeriesResponse)
async def get_player_weights(
    player_id: UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get weight time series for a player."""
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    query = text("""
        SELECT ws.date, wm.metric_value
        FROM wellness_metrics wm
        JOIN wellness_sessions ws ON ws.id = wm.wellness_session_id
        WHERE ws.player_id = :player_id
          AND wm.metric_key = 'body_weight_kg'
          AND ws.date >= :date_from
          AND ws.date <= :date_to
        ORDER BY ws.date ASC
    """)
    
    result = await session.execute(query, {
        "player_id": str(player_id),
        "date_from": date_from,
        "date_to": date_to,
    })
    rows = result.fetchall()
    
    series = [WeightPoint(date=row[0], weight_kg=float(row[1])) for row in rows]
    
    return WeightSeriesResponse(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        series=series,
    )


@router.get("/{player_id}/metrics", response_model=MetricsResponse)
async def get_player_metrics(
    player_id: UUID,
    metrics: Optional[str] = Query(None, description="Comma-separated metric keys"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    grouping: Literal["day", "week", "month"] = Query("day"),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get chronological rows of wellness and performance metrics."""
    
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Parse metrics or use defaults
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = [
            "sleep_hours", "sleep_quality", "fatigue", "stress", "mood", "doms",
            "resting_hr_bpm", "hrv_ms", "rpe_post", "total_distance", "hsr", 
            "sprint_count", "body_weight_kg"
        ]
    
    # Build query to get all metrics for date range
    # We'll query wellness and training separately, then combine
    query = text("""
        SELECT 
            ws.date,
            wm.metric_key,
            wm.metric_value
        FROM wellness_sessions ws
        LEFT JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND ws.date >= :date_from
          AND ws.date <= :date_to
          AND (wm.metric_key = ANY(:metric_list) OR wm.metric_key IS NULL)
        ORDER BY ws.date ASC
    """)
    
    result = await session.execute(query, {
        "player_id": str(player_id),
        "date_from": date_from,
        "date_to": date_to,
        "metric_list": metric_list,
    })
    wellness_rows = result.fetchall()
    
    # Also get training metrics
    training_query = text("""
        SELECT 
            ts.session_date::date as date,
            tm.metric_key,
            tm.metric_value
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        LEFT JOIN training_metrics tm ON tm.training_attendance_id = ta.id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date >= :date_from
          AND ts.session_date::date <= :date_to
          AND (tm.metric_key = ANY(:metric_list) OR tm.metric_key IS NULL)
        ORDER BY ts.session_date::date ASC
    """)
    
    training_result = await session.execute(training_query, {
        "player_id": str(player_id),
        "date_from": date_from,
        "date_to": date_to,
        "metric_list": metric_list,
    })
    training_rows = training_result.fetchall()
    
    # Combine into date-indexed dict
    rows_dict: dict[date, dict] = {}
    
    for row in wellness_rows:
        d = row[0]
        if d not in rows_dict:
            rows_dict[d] = {"date": d}
        if row[1]:  # metric_key
            rows_dict[d][row[1]] = float(row[2])
    
    for row in training_rows:
        d = row[0]
        if d not in rows_dict:
            rows_dict[d] = {"date": d}
        if row[1]:  # metric_key
            rows_dict[d][row[1]] = float(row[2])
    
    # Convert to list of MetricsRow
    rows_list = []
    for d in sorted(rows_dict.keys()):
        row_data = rows_dict[d]
        rows_list.append(MetricsRow(**row_data))
    
    return MetricsResponse(
        player_id=player_id,
        date_from=date_from,
        date_to=date_to,
        rows=rows_list,
    )


@router.post("/{player_id}/metrics", status_code=status.HTTP_201_CREATED)
async def create_player_metrics(
    player_id: UUID,
    metrics_data: MetricsCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Insert a set of metrics for a date."""
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get or create wellness session
    ws_result = await session.execute(
        select(WellnessSession).where(
            WellnessSession.player_id == player_id,
            WellnessSession.date == metrics_data.date
        )
    )
    ws = ws_result.scalar_one_or_none()
    
    if not ws:
        ws = WellnessSession(
            player_id=player_id,
            date=metrics_data.date,
            source=metrics_data.source or "manual",
            note=metrics_data.note,
            organization_id=org_id,
        )
        session.add(ws)
        await session.flush()
    
    # Add/update metrics
    for metric_entry in metrics_data.metrics:
        # Check if exists
        metric_result = await session.execute(
            select(WellnessMetric).where(
                WellnessMetric.wellness_session_id == ws.id,
                WellnessMetric.metric_key == metric_entry.metric_key
            )
        )
        metric = metric_result.scalar_one_or_none()
        
        if metric:
            metric.metric_value = metric_entry.metric_value
            if metric_entry.unit:
                metric.unit = metric_entry.unit
        else:
            metric = WellnessMetric(
                wellness_session_id=ws.id,
                metric_key=metric_entry.metric_key,
                metric_value=metric_entry.metric_value,
                unit=metric_entry.unit,
            )
            session.add(metric)
    
    await session.commit()
    return {"message": "Metrics created successfully", "date": metrics_data.date}


@router.get("/{player_id}/report", response_model=ReportResponse)
async def get_player_report(
    player_id: UUID,
    metric: str = Query(..., description="Metric key to analyze"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    grouping: Literal["day", "week", "month"] = Query("week"),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get metric analysis with KPI (min, max, avg, trend %)."""
    
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=90)
    
    # Map grouping to SQL
    grouping_map = {
        "day": "day",
        "week": "week",
        "month": "month"
    }
    bucket_sql = grouping_map.get(grouping, "week")
    
    # Query wellness metrics
    query = text(f"""
        SELECT 
            DATE_TRUNC('{bucket_sql}', ws.date)::date as bucket_start,
            AVG(wm.metric_value) as avg_value
        FROM wellness_sessions ws
        JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND wm.metric_key = :metric
          AND ws.date >= :date_from
          AND ws.date <= :date_to
        GROUP BY bucket_start
        ORDER BY bucket_start ASC
    """)
    
    result = await session.execute(query, {
        "player_id": str(player_id),
        "metric": metric,
        "date_from": date_from,
        "date_to": date_to,
    })
    wellness_rows = result.fetchall()
    
    # Also check training metrics
    training_query = text(f"""
        SELECT 
            DATE_TRUNC('{bucket_sql}', ts.session_date::date)::date as bucket_start,
            AVG(tm.metric_value) as avg_value
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        JOIN training_metrics tm ON tm.training_attendance_id = ta.id
        WHERE ta.player_id = :player_id
          AND tm.metric_key = :metric
          AND ts.session_date::date >= :date_from
          AND ts.session_date::date <= :date_to
        GROUP BY bucket_start
        ORDER BY bucket_start ASC
    """)
    
    training_result = await session.execute(training_query, {
        "player_id": str(player_id),
        "metric": metric,
        "date_from": date_from,
        "date_to": date_to,
    })
    training_rows = training_result.fetchall()
    
    # Combine results
    series_dict: dict[date, float] = {}
    for row in wellness_rows:
        series_dict[row[0]] = float(row[1]) if row[1] else None
    for row in training_rows:
        if row[0] not in series_dict or series_dict[row[0]] is None:
            series_dict[row[0]] = float(row[1]) if row[1] else None
    
    # Convert to sorted list
    series = [
        ReportPoint(bucket_start=d, value=series_dict[d])
        for d in sorted(series_dict.keys())
    ]
    
    # Calculate KPI
    values = [s.value for s in series if s.value is not None]
    if not values:
        kpi = ReportKPI(metric=metric)
    else:
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        # Trend: % change from first to last
        if len(values) >= 2:
            first_val = values[0]
            last_val = values[-1]
            if first_val != 0:
                trend_pct = ((last_val - first_val) / first_val) * 100
            else:
                trend_pct = None
        else:
            trend_pct = None
        
        kpi = ReportKPI(
            metric=metric,
            min_value=min_val,
            max_value=max_val,
            avg_value=avg_val,
            trend_pct=trend_pct,
        )
    
    return ReportResponse(
        player_id=player_id,
        metric=metric,
        date_from=date_from,
        date_to=date_to,
        grouping=grouping,
        series=series,
        kpi=kpi,
    )

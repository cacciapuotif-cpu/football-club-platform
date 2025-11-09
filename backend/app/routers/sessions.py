"""Sessions API - read endpoints."""

from datetime import datetime, timedelta
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.models.sessions_wellness import (
    Alert,
    Prediction,
    Session,
    SessionParticipation,
    SessionType,
    WellnessReading,
)
from app.models.user import User
from app.schemas.sessions_wellness import (
    SessionDetail,
    SessionListItem,
    SessionParticipationItem,
    SessionWellnessSnapshot,
    SnapshotAlert,
    SnapshotPrediction,
    WellnessMetricPoint,
    SessionsPage,
)

router = APIRouter()


@router.get(
    "/",
    response_model=SessionsPage,
    summary="List sessions",
    description="Return paginated sessions filtered by team, type, and date window.",
)
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    team_id: UUID | None = Query(None, alias="teamId"),
    session_type: Optional[str] = Query(None, alias="type", description="Session type (training, match, recovery, other)"),
    from_ts: Optional[datetime] = Query(None, alias="from"),
    to_ts: Optional[datetime] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, alias="pageSize", ge=1, le=200),
) -> SessionsPage:
    filters = [Session.tenant_id == current_user.organization_id]

    if team_id:
        filters.append(Session.team_id == team_id)

    if session_type:
        try:
            session_type_enum = SessionType(session_type.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported session type: {session_type}",
            ) from exc
        filters.append(Session.type == session_type_enum)

    if from_ts:
        filters.append(Session.start_ts >= from_ts)
    if to_ts:
        filters.append(Session.start_ts <= to_ts)

    count_stmt = select(func.count()).select_from(Session).where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size

    data_stmt = (
        select(Session)
        .where(*filters)
        .order_by(Session.start_ts.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(data_stmt)
    sessions = result.scalars().all()

    items = [SessionListItem.model_validate(obj) for obj in sessions]
    has_next = offset + len(items) < total

    return SessionsPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        has_next=has_next,
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
    summary="Get session detail",
    description="Retrieve session metadata and participation for the specified session.",
)
async def get_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionDetail:
    session_stmt = select(Session).where(
        Session.session_id == session_id,
        Session.tenant_id == current_user.organization_id,
    )
    result = await session.execute(session_stmt)
    session_row = result.scalar_one_or_none()
    if not session_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    participation_stmt = select(SessionParticipation).where(
        SessionParticipation.session_id == session_id,
        SessionParticipation.tenant_id == current_user.organization_id,
    )
    participation_rows = (await session.execute(participation_stmt)).scalars().all()

    return SessionDetail(
        session=SessionListItem.model_validate(session_row),
        participation=[SessionParticipationItem.model_validate(row) for row in participation_rows],
    )


@router.get(
    "/{session_id}/wellness_snapshot",
    response_model=SessionWellnessSnapshot,
    summary="Session wellness snapshot",
    description="Summarise wellness metrics, predictions, and alerts around the session window for participating athletes.",
)
async def get_session_wellness_snapshot(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    window_days: int = Query(2, ge=1, le=7),
) -> SessionWellnessSnapshot:
    session_stmt = select(Session).where(
        Session.session_id == session_id,
        Session.tenant_id == current_user.organization_id,
    )
    result = await session.execute(session_stmt)
    session_row = result.scalar_one_or_none()
    if not session_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    participation_stmt = select(SessionParticipation).where(
        SessionParticipation.session_id == session_id,
        SessionParticipation.tenant_id == current_user.organization_id,
    )
    participation_rows = (await session.execute(participation_stmt)).scalars().all()
    athlete_ids = [row.athlete_id for row in participation_rows]

    window_start = session_row.start_ts - timedelta(days=window_days)
    window_end = session_row.start_ts + timedelta(days=window_days)

    metrics: list[WellnessMetricPoint] = []
    predictions: list[SnapshotPrediction] = []
    alerts: list[SnapshotAlert] = []

    if athlete_ids:
        metrics_stmt = select(WellnessReading).where(
            WellnessReading.tenant_id == current_user.organization_id,
            WellnessReading.athlete_id.in_(athlete_ids),
            WellnessReading.event_ts >= window_start,
            WellnessReading.event_ts <= window_end,
        )
        metric_rows = (await session.execute(metrics_stmt)).scalars().all()
        metrics = [
            WellnessMetricPoint.model_validate(
                {
                    "athlete_id": row.athlete_id,
                    "metric": row.metric,
                    "value": row.value,
                    "unit": row.unit,
                    "event_ts": row.event_ts,
                }
            )
            for row in metric_rows
        ]

        predictions_stmt = select(Prediction).where(
            Prediction.tenant_id == current_user.organization_id,
            Prediction.athlete_id.in_(athlete_ids),
            Prediction.event_ts >= window_start,
            Prediction.event_ts <= window_end,
        )
        prediction_rows = (await session.execute(predictions_stmt)).scalars().all()
        predictions = [
            SnapshotPrediction.model_validate(
                {
                    "athlete_id": row.athlete_id,
                    "score": row.score,
                    "severity": row.severity,
                    "model_version": row.model_version,
                    "event_ts": row.event_ts,
                    "drivers": row.drivers,
                }
            )
            for row in prediction_rows
        ]

        alerts_stmt = select(Alert).where(
            Alert.tenant_id == current_user.organization_id,
            Alert.athlete_id.in_(athlete_ids),
            Alert.opened_at >= window_start,
            Alert.opened_at <= window_end,
        )
        alert_rows = (await session.execute(alerts_stmt)).scalars().all()
        alerts = [
            SnapshotAlert.model_validate(
                {
                    "id": row.id,
                    "athlete_id": row.athlete_id,
                    "session_id": row.session_id,
                    "status": row.status,
                    "severity": row.severity,
                    "opened_at": row.opened_at,
                    "closed_at": row.closed_at,
                    "policy_id": row.policy_id,
                }
            )
            for row in alert_rows
        ]

    return SessionWellnessSnapshot(
        session_id=session_id,
        window_days=window_days,
        window_start=window_start,
        window_end=window_end,
        athletes=athlete_ids,
        metrics=metrics,
        predictions=predictions,
        alerts=alerts,
    )

"""Wellness APIs for Sessions & Wellness domain (Team A/B foundations)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.models.sessions_wellness import (
    Alert,
    AlertStatus,
    Athlete,
    Feature,
    Prediction,
    PredictionSeverity,
    Session,
    SessionParticipation,
    WellnessPolicy,
)
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.schemas.sessions_wellness import (
    AthleteContextResponse,
    AthleteHeatmapCell,
    AthleteReadinessSeries,
    ContextSessionSummary,
    FeatureSnapshot,
    PlayerSummary,
    ReadinessTrendPoint,
    SnapshotAlert,
    SnapshotPrediction,
    TeamWellnessHeatmap,
    WellnessPolicyCreate,
    WellnessPolicyResponse,
)

router = APIRouter()


def _day_bounds(target: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


async def _fetch_athletes_for_players(
    session: AsyncSession, tenant_id: UUID, player_ids: Iterable[UUID]
) -> list[Athlete]:
    if not player_ids:
        return []
    stmt = select(Athlete).where(
        Athlete.tenant_id == tenant_id,
        Athlete.player_id.in_(list(player_ids)),
    )
    return list((await session.execute(stmt)).scalars().all())


@router.get(
    "/teams/{team_id}/heatmap",
    response_model=TeamWellnessHeatmap,
    summary="Team wellness heatmap",
    description="Return readiness and risk snapshot for all athletes in a team on the specified date.",
)
async def get_team_heatmap(
    team_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_date: date = Query(default_factory=date.today, description="Date for the heatmap"),
) -> TeamWellnessHeatmap:
    team_stmt = select(Team).where(
        Team.id == team_id,
        Team.organization_id == current_user.organization_id,
    )
    team = (await session.execute(team_stmt)).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    players_stmt = select(Player).where(
        Player.team_id == team_id,
        Player.organization_id == current_user.organization_id,
    )
    players = list((await session.execute(players_stmt)).scalars().all())
    player_map = {player.id: player for player in players}

    athletes = await _fetch_athletes_for_players(session, current_user.organization_id, player_map.keys())
    athlete_ids = [athlete.athlete_id for athlete in athletes]
    athlete_player_lookup = {athlete.athlete_id: athlete.player_id for athlete in athletes}

    day_start, day_end = _day_bounds(target_date)
    prev_start = day_start - timedelta(days=1)
    prev_end = day_start

    cells: list[AthleteHeatmapCell] = []
    if not athletes:
        return TeamWellnessHeatmap(team_id=team_id, date=target_date, cells=cells)

    readiness_stmt = select(Feature).where(
        Feature.tenant_id == current_user.organization_id,
        Feature.athlete_id.in_(athlete_ids),
        Feature.feature_name == "readiness_score",
        Feature.event_ts >= day_start,
        Feature.event_ts < day_end,
    )
    readiness_rows = list((await session.execute(readiness_stmt)).scalars().all())
    readiness_map = {(row.athlete_id, row.feature_name): row for row in readiness_rows}

    prev_stmt = select(Feature).where(
        Feature.tenant_id == current_user.organization_id,
        Feature.athlete_id.in_(athlete_ids),
        Feature.feature_name == "readiness_score",
        Feature.event_ts >= prev_start,
        Feature.event_ts < prev_end,
    )
    prev_rows = list((await session.execute(prev_stmt)).scalars().all())
    prev_map = {(row.athlete_id, row.feature_name): row for row in prev_rows}

    predictions_stmt = select(Prediction).where(
        Prediction.tenant_id == current_user.organization_id,
        Prediction.athlete_id.in_(athlete_ids),
        Prediction.event_ts >= day_start,
        Prediction.event_ts < day_end,
    )
    prediction_rows = list((await session.execute(predictions_stmt)).scalars().all())
    prediction_map = {row.athlete_id: row for row in prediction_rows}

    alerts_stmt = select(Alert).where(
        Alert.tenant_id == current_user.organization_id,
        Alert.athlete_id.in_(athlete_ids),
        Alert.opened_at >= day_start - timedelta(days=1),
        Alert.opened_at < day_end + timedelta(days=1),
    )
    alert_rows = list((await session.execute(alerts_stmt)).scalars().all())
    alerts_group: dict[UUID, list[Alert]] = {}
    for alert in alert_rows:
        alerts_group.setdefault(alert.athlete_id, []).append(alert)

    for athlete in athletes:
        player = player_map.get(athlete.player_id) if athlete.player_id else None
        current_feature = readiness_map.get((athlete.athlete_id, "readiness_score"))
        prev_feature = prev_map.get((athlete.athlete_id, "readiness_score"))
        prediction = prediction_map.get(athlete.athlete_id)
        related_alerts = alerts_group.get(athlete.athlete_id, [])

        full_name = None
        role = None
        team_ref = None
        if player:
            full_name = f"{player.first_name} {player.last_name}".strip()
            role = player.role_primary.value if hasattr(player.role_primary, "value") else str(player.role_primary)
            team_ref = player.team_id

        readiness_score = current_feature.feature_value if current_feature else None
        readiness_delta = None
        if current_feature and prev_feature:
            readiness_delta = round(current_feature.feature_value - prev_feature.feature_value, 2)

        latest_alert_at = (
            max(alert.opened_at for alert in related_alerts) if related_alerts else None
        )

        cells.append(
            AthleteHeatmapCell(
                athlete_id=athlete.athlete_id,
                player_id=player.id if player else None,
                full_name=full_name,
                role=role,
                readiness_score=round(readiness_score, 2) if readiness_score is not None else None,
                risk_severity=prediction.severity if prediction else None,
                alerts_count=len(related_alerts),
                latest_alert_at=latest_alert_at,
                readiness_delta=readiness_delta,
            )
        )

    return TeamWellnessHeatmap(team_id=team_id, date=target_date, cells=cells)


@router.get(
    "/athletes/{athlete_id}/readiness",
    response_model=AthleteReadinessSeries,
    summary="Athlete readiness trend",
)
async def get_athlete_readiness(
    athlete_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
) -> AthleteReadinessSeries:
    athlete_stmt = select(Athlete).where(
        Athlete.athlete_id == athlete_id,
        Athlete.tenant_id == current_user.organization_id,
    )
    athlete = (await session.execute(athlete_stmt)).scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    date_from = from_date or (date.today() - timedelta(days=30))
    date_to = to_date or date.today()

    range_start, _ = _day_bounds(date_from)
    _, range_end = _day_bounds(date_to)

    features_stmt = (
        select(Feature)
        .where(
            Feature.tenant_id == current_user.organization_id,
            Feature.athlete_id == athlete_id,
            Feature.feature_name == "readiness_score",
            Feature.event_ts >= range_start,
            Feature.event_ts < range_end,
        )
        .order_by(Feature.event_ts.asc())
    )
    feature_rows = list((await session.execute(features_stmt)).scalars().all())

    predictions_stmt = (
        select(Prediction)
        .where(
            Prediction.tenant_id == current_user.organization_id,
            Prediction.athlete_id == athlete_id,
            Prediction.event_ts >= range_start,
            Prediction.event_ts < range_end,
        )
        .order_by(Prediction.event_ts.asc())
    )
    prediction_rows = list((await session.execute(predictions_stmt)).scalars().all())
    prediction_map = {row.event_ts: row for row in prediction_rows}

    points = [
        ReadinessTrendPoint(
            event_ts=row.event_ts,
            readiness_score=round(row.feature_value, 2),
            severity=prediction_map.get(row.event_ts).severity if prediction_map.get(row.event_ts) else None,
        )
        for row in feature_rows
    ]

    return AthleteReadinessSeries(athlete_id=athlete_id, points=points)


@router.get(
    "/athletes/{athlete_id}/context",
    response_model=AthleteContextResponse,
    summary="Athlete context snapshot",
)
async def get_athlete_context(
    athlete_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(7, ge=1, le=30),
) -> AthleteContextResponse:
    athlete_stmt = select(Athlete).where(
        Athlete.athlete_id == athlete_id,
        Athlete.tenant_id == current_user.organization_id,
    )
    athlete = (await session.execute(athlete_stmt)).scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    now = datetime.now(timezone.utc)
    range_start = now - timedelta(days=days)

    player = None
    if athlete.player_id:
        player_stmt = select(Player).where(
            Player.id == athlete.player_id,
            Player.organization_id == current_user.organization_id,
        )
        player = (await session.execute(player_stmt)).scalar_one_or_none()

    feature_names = [
        "readiness_score",
        "acute_chronic_ratio_7_28",
        "rolling_hrv_baseline_28d",
        "sleep_debt_hours_7d",
        "wellness_survey_z",
    ]

    features_stmt = (
        select(Feature)
        .where(
            Feature.tenant_id == current_user.organization_id,
            Feature.athlete_id == athlete_id,
            Feature.feature_name.in_(feature_names),
            Feature.event_ts >= range_start - timedelta(days=7),
            Feature.event_ts <= now,
        )
        .order_by(Feature.event_ts.asc())
    )
    feature_rows = list((await session.execute(features_stmt)).scalars().all())

    latest_features: dict[str, Feature] = {}
    for feature in feature_rows:
        latest_features[feature.feature_name] = feature

    readiness_trend_series = await get_athlete_readiness(
        athlete_id=athlete_id,
        current_user=current_user,
        session=session,
        from_date=(now - timedelta(days=days)).date(),
        to_date=now.date(),
    )

    sessions_stmt = (
        select(Session, SessionParticipation)
        .join(
            SessionParticipation,
            and_(
                SessionParticipation.session_id == Session.session_id,
                SessionParticipation.tenant_id == current_user.organization_id,
            ),
        )
        .where(
            SessionParticipation.athlete_id == athlete_id,
            SessionParticipation.tenant_id == current_user.organization_id,
            Session.start_ts >= range_start,
            Session.start_ts <= now,
        )
        .order_by(Session.start_ts.desc())
    )
    session_rows = list((await session.execute(sessions_stmt)).all())
    recent_sessions = [
        ContextSessionSummary(
            session_id=session_obj.session_id,
            start_ts=session_obj.start_ts,
            type=session_obj.type,
            load=participation.load,
            rpe=participation.rpe,
            minutes=None,
        )
        for session_obj, participation in session_rows
    ]

    alerts_stmt = select(Alert).where(
        Alert.tenant_id == current_user.organization_id,
        Alert.athlete_id == athlete_id,
        Alert.opened_at >= range_start,
        Alert.opened_at <= now,
    )
    alert_rows = list((await session.execute(alerts_stmt)).scalars().all())
    alerts = [
        SnapshotAlert(
            id=alert.id,
            athlete_id=alert.athlete_id,
            session_id=alert.session_id,
            status=alert.status,
            severity=alert.severity,
            opened_at=alert.opened_at,
            closed_at=alert.closed_at,
            policy_id=alert.policy_id,
        )
        for alert in alert_rows
    ]

    latest_feature_snapshots = [
        FeatureSnapshot(
            feature_name=name,
            feature_value=round(feature.feature_value, 3),
            event_ts=feature.event_ts,
        )
        for name, feature in latest_features.items()
        if feature is not None
    ]

    return AthleteContextResponse(
        athlete_id=athlete_id,
        player=PlayerSummary(
            player_id=player.id if player else None,
            full_name=f"{player.first_name} {player.last_name}".strip() if player else None,
            role=player.role_primary.value if player and hasattr(player.role_primary, "value") else (str(player.role_primary) if player else None),
            team_id=player.team_id if player else None,
        ),
        range_start=range_start,
        range_end=now,
        latest_features=latest_feature_snapshots,
        readiness_trend=readiness_trend_series.points,
        recent_sessions=recent_sessions,
        alerts=alerts,
    )


@router.post(
    "/policies",
    response_model=WellnessPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create wellness policy",
)
async def create_wellness_policy(
    payload: WellnessPolicyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WellnessPolicyResponse:
    policy = WellnessPolicy(
        tenant_id=current_user.organization_id,
        name=payload.name,
        description=payload.description,
        thresholds=payload.thresholds,
        cooldown_hours=payload.cooldown_hours,
        min_data_completeness=payload.min_data_completeness,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)
    return WellnessPolicyResponse.model_validate(policy)


@router.get(
    "/policies",
    response_model=list[WellnessPolicyResponse],
    summary="List wellness policies",
)
async def list_wellness_policies(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[WellnessPolicyResponse]:
    stmt = select(WellnessPolicy).where(WellnessPolicy.tenant_id == current_user.organization_id).order_by(
        WellnessPolicy.created_at.desc()
    )
    policies = list((await session.execute(stmt)).scalars().all())
    return [WellnessPolicyResponse.model_validate(policy) for policy in policies]


@router.get(
    "/policies/{policy_id}",
    response_model=WellnessPolicyResponse,
    summary="Get wellness policy",
)
async def get_wellness_policy(
    policy_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WellnessPolicyResponse:
    stmt = select(WellnessPolicy).where(
        WellnessPolicy.id == policy_id,
        WellnessPolicy.tenant_id == current_user.organization_id,
    )
    policy = (await session.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return WellnessPolicyResponse.model_validate(policy)


@router.patch(
    "/policies/{policy_id}",
    response_model=WellnessPolicyResponse,
    summary="Update wellness policy",
)
async def update_wellness_policy(
    policy_id: UUID,
    payload: WellnessPolicyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WellnessPolicyResponse:
    stmt = select(WellnessPolicy).where(
        WellnessPolicy.id == policy_id,
        WellnessPolicy.tenant_id == current_user.organization_id,
    )
    policy = (await session.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    policy.name = payload.name
    policy.description = payload.description
    policy.thresholds = payload.thresholds
    policy.cooldown_hours = payload.cooldown_hours
    policy.min_data_completeness = payload.min_data_completeness
    await session.commit()
    await session.refresh(policy)
    return WellnessPolicyResponse.model_validate(policy)


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete wellness policy",
)
async def delete_wellness_policy(
    policy_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    stmt = select(WellnessPolicy).where(
        WellnessPolicy.id == policy_id,
        WellnessPolicy.tenant_id == current_user.organization_id,
    )
    policy = (await session.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    await session.delete(policy)
    await session.commit()
    return None


@router.post(
    "/alerts/{alert_id}/ack",
    summary="Acknowledge alert",
)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    stmt = select(Alert).where(
        Alert.id == alert_id,
        Alert.tenant_id == current_user.organization_id,
    )
    alert = (await session.execute(stmt)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.ack_by = current_user.id
    alert.closed_at = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "ok", "message": "Alert acknowledged"}

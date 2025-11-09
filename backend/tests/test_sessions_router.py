"""Tests for sessions router endpoints (pure unit-level with mocked session)."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from fastapi import HTTPException

from app.models.sessions_wellness import (
    Alert,
    AlertStatus,
    Prediction,
    PredictionSeverity,
    Session,
    SessionParticipation,
    SessionParticipationStatus,
    SessionType,
    WellnessReading,
)
from app.routers import sessions as sessions_router


class _FakeScalarSequence:
    def __init__(self, data: list | None):
        self._data = data or []

    def all(self) -> list:
        return list(self._data)


class _FakeResult:
    def __init__(self, scalar=None, list_data: list | None = None):
        self._scalar = scalar
        self._list = list_data or []

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return _FakeScalarSequence(self._list)


class _FakeAsyncSession:
    def __init__(self, results: list[_FakeResult]):
        self._results = results
        self._index = 0

    async def execute(self, stmt):  # pragma: no cover - behaviour verified via tests
        if self._index >= len(self._results):
            raise AssertionError("execute called more times than expected")
        result = self._results[self._index]
        self._index += 1
        return result


class _FakeUser:
    def __init__(self, organization_id: UUID):
        self.organization_id = organization_id


@pytest.mark.asyncio
async def test_list_sessions_returns_paginated_items():
    tenant_id = uuid4()
    now = datetime.utcnow()
    sessions = [
        Session(
            session_id=uuid4(),
            tenant_id=tenant_id,
            team_id=uuid4(),
            type=SessionType.TRAINING,
            start_ts=now,
            end_ts=now + timedelta(hours=2),
            rpe_avg=4.5,
            load=180.0,
            notes="Tattico",
            created_at=now,
        ),
        Session(
            session_id=uuid4(),
            tenant_id=tenant_id,
            team_id=uuid4(),
            type=SessionType.MATCH,
            start_ts=now - timedelta(days=1),
            end_ts=now - timedelta(days=1, hours=-2),
            rpe_avg=5.5,
            load=220.0,
            notes="Amichevole",
            created_at=now,
        ),
    ]
    fake_session = _FakeAsyncSession(
        [
            _FakeResult(scalar=len(sessions)),
            _FakeResult(list_data=sessions),
        ]
    )

    payload = await sessions_router.list_sessions(
        current_user=_FakeUser(tenant_id),
        session=fake_session,
        page=1,
        page_size=25,
    )

    assert payload.total == 2
    assert payload.page == 1
    assert payload.page_size == 25
    assert payload.has_next is False
    assert len(payload.items) == 2
    assert payload.items[0].team_id == sessions[0].team_id


@pytest.mark.asyncio
async def test_list_sessions_invalid_type_raises():
    tenant_id = uuid4()
    fake_session = _FakeAsyncSession([_FakeResult(scalar=0), _FakeResult(list_data=[])])

    with pytest.raises(HTTPException) as exc:
        await sessions_router.list_sessions(
            current_user=_FakeUser(tenant_id),
            session=fake_session,
            session_type="invalid",
        )

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_get_session_details_success():
    tenant_id = uuid4()
    session_id = uuid4()
    now = datetime.utcnow()
    training_session = Session(
        session_id=session_id,
        tenant_id=tenant_id,
        team_id=uuid4(),
        type=SessionType.TRAINING,
        start_ts=now,
        end_ts=now + timedelta(hours=2),
        created_at=now,
    )
    participations = [
        SessionParticipation(
            id=uuid4(),
            tenant_id=tenant_id,
            session_id=session_id,
            athlete_id=uuid4(),
            status=SessionParticipationStatus.COMPLETED,
        )
    ]
    fake_session = _FakeAsyncSession(
        [
            _FakeResult(scalar=training_session),
            _FakeResult(list_data=participations),
        ]
    )

    detail = await sessions_router.get_session(
        session_id=session_id,
        current_user=_FakeUser(tenant_id),
        session=fake_session,
    )

    assert detail.session.session_id == session_id
    assert len(detail.participation) == 1
    assert detail.participation[0].athlete_id == participations[0].athlete_id


@pytest.mark.asyncio
async def test_get_session_details_not_found():
    fake_session = _FakeAsyncSession([_FakeResult(scalar=None)])

    with pytest.raises(HTTPException) as exc:
        await sessions_router.get_session(
            session_id=uuid4(),
            current_user=_FakeUser(uuid4()),
            session=fake_session,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_session_wellness_snapshot_collects_data():
    tenant_id = uuid4()
    session_id = uuid4()
    athlete_id = uuid4()
    now = datetime.utcnow()
    training_session = Session(
        session_id=session_id,
        tenant_id=tenant_id,
        team_id=uuid4(),
        type=SessionType.TRAINING,
        start_ts=now,
        end_ts=now + timedelta(hours=2),
        created_at=now,
    )
    participation = SessionParticipation(
        id=uuid4(),
        tenant_id=tenant_id,
        session_id=session_id,
        athlete_id=athlete_id,
        status=SessionParticipationStatus.COMPLETED,
    )
    reading = WellnessReading(
        id=uuid4(),
        tenant_id=tenant_id,
        athlete_id=athlete_id,
        source="wearable",
        metric="hrv",
        value=85.0,
        unit="ms",
        event_ts=now - timedelta(hours=12),
        ingest_ts=now - timedelta(hours=11),
        quality_score=0.9,
        created_at=now - timedelta(hours=11),
    )
    prediction = Prediction(
        id=uuid4(),
        tenant_id=tenant_id,
        athlete_id=athlete_id,
        model_version="1.0.0",
        score=72.5,
        severity=PredictionSeverity.MEDIUM,
        drivers={"hrv_z": -1.2},
        event_ts=now - timedelta(hours=6),
        created_at=now - timedelta(hours=6),
    )
    alert = Alert(
        id=uuid4(),
        tenant_id=tenant_id,
        athlete_id=athlete_id,
        session_id=session_id,
        status=AlertStatus.OPEN,
        severity=PredictionSeverity.HIGH,
        policy_id="policy-001",
        opened_at=now - timedelta(hours=5),
        created_at=now - timedelta(hours=5),
    )

    fake_session = _FakeAsyncSession(
        [
            _FakeResult(scalar=training_session),
            _FakeResult(list_data=[participation]),
            _FakeResult(list_data=[reading]),
            _FakeResult(list_data=[prediction]),
            _FakeResult(list_data=[alert]),
        ]
    )

    snapshot = await sessions_router.get_session_wellness_snapshot(
        session_id=session_id,
        current_user=_FakeUser(tenant_id),
        session=fake_session,
        window_days=2,
    )

    assert snapshot.session_id == session_id
    assert snapshot.window_days == 2
    assert snapshot.window_start == training_session.start_ts - timedelta(days=2)
    assert snapshot.window_end == training_session.start_ts + timedelta(days=2)
    assert snapshot.athletes == [athlete_id]
    assert len(snapshot.metrics) == 1 and snapshot.metrics[0].metric == "hrv"
    assert len(snapshot.predictions) == 1 and snapshot.predictions[0].severity == PredictionSeverity.MEDIUM
    assert len(snapshot.alerts) == 1 and snapshot.alerts[0].status == AlertStatus.OPEN


@pytest.mark.asyncio
async def test_get_session_wellness_snapshot_session_missing():
    fake_session = _FakeAsyncSession([_FakeResult(scalar=None)])

    with pytest.raises(HTTPException) as exc:
        await sessions_router.get_session_wellness_snapshot(
            session_id=uuid4(),
            current_user=_FakeUser(uuid4()),
            session=fake_session,
        )

    assert exc.value.status_code == 404


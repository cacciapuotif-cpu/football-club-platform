from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.main import app
from app.ml.inference_service import ensure_model_ready
from app.ml.pipelines.train_readiness import train_readiness_model


@pytest.fixture(scope="module", autouse=True)
def _prepare_model() -> None:
    train_readiness_model(force=True)
    ensure_model_ready()


def test_predict_endpoint_returns_payload(monkeypatch):
    client = TestClient(app)

    monkeypatch.setenv("SKIP_AUTH", "true")

    response = client.post(
        "/api/v1/ml/readiness/predict",
        json={
            "age_years": 17,
            "position_code": 2,
            "session_load": 520.0,
            "wellness_score": 78.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "expected_performance" in payload
    assert 0 <= payload["expected_performance"] <= 100
    assert payload["model_version"].startswith("sklearn-readiness")


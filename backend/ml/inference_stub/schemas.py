from __future__ import annotations

from datetime import date
from typing import List, Literal, TypedDict


class ReadinessFeaturePayload(TypedDict):
    tenant_id: str
    athlete_id: str
    event_date: date
    features: List[dict]


class ReadinessPredictionResponse(TypedDict):
    athlete_id: str
    event_date: date
    readiness_score: float
    risk_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    drivers: List[dict]


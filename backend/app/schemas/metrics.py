"""Schemas for player metrics (ACWR, Monotony, Strain, Readiness)."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class MetricDaily(BaseModel):
    """Daily metrics for a player."""
    date: date
    acwr: Optional[float] = None
    monotony: Optional[float] = None
    strain: Optional[float] = None
    readiness: Optional[float] = None

    class Config:
        from_attributes = True


class PlayerMetricsSummary(BaseModel):
    """Summary of metrics for a player over time."""
    player_id: UUID
    metrics: List[MetricDaily]

    class Config:
        from_attributes = True


class PlayerMetricsLatest(BaseModel):
    """Latest metrics for a player."""
    player_id: UUID
    date: date
    acwr: Optional[float] = None
    monotony: Optional[float] = None
    strain: Optional[float] = None
    readiness: Optional[float] = None

    class Config:
        from_attributes = True

"""Pydantic schemas for ML Analytics endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PlayerMLSummary(BaseModel):
    """Player ML summary with advanced metrics."""
    player_id: UUID
    last_10_matches: int
    avg_xg: float
    avg_key_passes: float
    avg_duels_won: float
    trend_form_last_10: float

    class Config:
        from_attributes = True


class PlayerPredictionOut(BaseModel):
    """Player prediction output."""
    player_id: UUID
    date: date
    target: str
    model_name: str
    model_version: str
    y_pred: Optional[float] = None
    y_proba: Optional[float] = None

    class Config:
        from_attributes = True


class PredictionsListResponse(BaseModel):
    """List of predictions for a player."""
    player_id: UUID
    items: list[PlayerPredictionOut]


class TrainModelsResponse(BaseModel):
    """Response from model training."""
    status: str
    result: dict


class IngestionResponse(BaseModel):
    """Response from data ingestion."""
    status: str
    message: str

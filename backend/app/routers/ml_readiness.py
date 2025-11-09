"""Readiness prediction endpoints powered by scikit-learn."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.ml.inference_service import ensure_model_ready
from app.models.ml import MLPrediction, OverloadRiskLevel, ThresholdLevel
from app.models.player import Player
from app.models.user import User

router = APIRouter(tags=["ML Readiness"])


class FeaturePayload(BaseModel):
    age_years: float = Field(..., ge=10, le=45)
    position_code: int = Field(..., ge=0, le=4)
    session_load: float = Field(..., ge=0)
    wellness_score: float = Field(..., ge=0, le=100)


class PredictionPayload(BaseModel):
    expected_performance: float
    confidence_lower: float
    confidence_upper: float
    overload_probability: float
    overload_risk_level: OverloadRiskLevel
    threshold: ThresholdLevel
    feature_importances: Dict[str, float]
    model_version: str


class ReadinessResponse(PredictionPayload):
    player_id: UUID
    prediction_date: datetime


@router.post("/readiness/predict", response_model=PredictionPayload)
async def predict_readiness(
    features: FeaturePayload,
    _: Annotated[User, Depends(get_current_user)],
) -> PredictionPayload:
    service = ensure_model_ready()
    result = service.predict(features.model_dump())
    return PredictionPayload(
        expected_performance=result.expected_performance,
        confidence_lower=result.confidence_lower,
        confidence_upper=result.confidence_upper,
        overload_probability=result.overload_probability,
        overload_risk_level=result.overload_risk_level,
        threshold=result.threshold,
        feature_importances=result.feature_importances,
        model_version=result.model_version,
    )


@router.get("/readiness/{player_id}", response_model=ReadinessResponse)
async def get_player_readiness(
    player_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReadinessResponse:
    query = (
        select(MLPrediction)
        .where(MLPrediction.player_id == player_id)
        .order_by(MLPrediction.prediction_date.desc())
        .limit(1)
    )
    result = await session.execute(query)
    prediction: Optional[MLPrediction] = result.scalar_one_or_none()
    if prediction is None:
        player = await session.get(Player, player_id)
        if player is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions available for this player",
        )

    return ReadinessResponse(
        player_id=player_id,
        prediction_date=prediction.prediction_date,
        expected_performance=prediction.expected_performance,
        confidence_lower=prediction.confidence_lower,
        confidence_upper=prediction.confidence_upper,
        overload_probability=prediction.overload_probability,
        overload_risk_level=prediction.overload_risk_level,
        threshold=prediction.threshold,
        feature_importances=prediction.feature_importances,
        model_version=prediction.model_version,
    )


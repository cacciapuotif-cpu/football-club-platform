"""
Predictions API Router - Wrapper per ML predictions
Team 2 Implementation
"""

from datetime import date, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()


class PredictionResponse(BaseModel):
    """Injury risk prediction response."""
    player_id: UUID
    prediction_date: date
    horizon_days: Literal[7, 14, 28]
    risk_score: float  # 0-1
    risk_class: Literal["Low", "Medium", "High", "Very High"]
    model_version: str


class FeatureImportance(BaseModel):
    """Feature importance for explainability."""
    feature: str
    importance: float


@router.get("/{player_id}", response_model=PredictionResponse)
async def get_player_prediction(
    player_id: UUID,
    horizon: int = Query(7, description="Prediction horizon in days (7, 14, or 28)", ge=7, le=28),
    session: AsyncSession = Depends(get_session),
):
    """
    Get injury risk prediction for a player.

    **Team 2 Implementation**: Stub endpoint returning mock data.
    Team 3 will integrate with actual ML models from progress_ml router.

    **Parameters**:
    - player_id: Player UUID
    - horizon: Prediction horizon (7, 14, or 28 days)

    **Returns**:
    - Risk score (0-1)
    - Risk classification
    - Model metadata
    """
    # Verify player exists
    from sqlmodel import select
    from app.models.player import Player

    result = await session.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    # Validate horizon value
    if horizon not in [7, 14, 28]:
        raise HTTPException(status_code=422, detail="Horizon must be 7, 14, or 28 days")

    # Mock prediction (Team 2 stub)
    # Team 3 will call actual ML service
    import hashlib
    player_hash = int(hashlib.md5(str(player_id).encode()).hexdigest(), 16)
    risk_score = (player_hash % 100) / 100.0  # Deterministic mock based on player_id

    # Classify risk
    if risk_score < 0.25:
        risk_class = "Low"
    elif risk_score < 0.50:
        risk_class = "Medium"
    elif risk_score < 0.75:
        risk_class = "High"
    else:
        risk_class = "Very High"

    return PredictionResponse(
        player_id=player_id,
        prediction_date=date.today(),
        horizon_days=horizon,
        risk_score=risk_score,
        risk_class=risk_class,
        model_version="stub-v0.1.0-team2"
    )


@router.get("/{player_id}/features", response_model=list[FeatureImportance])
async def get_prediction_features(
    player_id: UUID,
    horizon: Literal[7, 14, 28] = Query(7),
    session: AsyncSession = Depends(get_session),
):
    """
    Get feature importances for prediction explainability (SHAP-like).

    **Team 2 Implementation**: Mock SHAP values.
    Team 3 will integrate actual SHAP from ML models.
    """
    # Verify player exists
    from sqlmodel import select
    from app.models.player import Player

    result = await session.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    # Mock feature importances
    return [
        FeatureImportance(feature="acwr", importance=0.32),
        FeatureImportance(feature="sleep_quality", importance=0.18),
        FeatureImportance(feature="wellness_fatigue", importance=0.15),
        FeatureImportance(feature="training_load_7d", importance=0.12),
        FeatureImportance(feature="match_density", importance=0.10),
        FeatureImportance(feature="doms_score", importance=0.08),
        FeatureImportance(feature="stress_level", importance=0.05),
    ]

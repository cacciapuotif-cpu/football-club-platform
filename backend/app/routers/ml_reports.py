"""ML Reports Router - Predictive analytics and performance forecasting endpoints."""

import logging
from datetime import date
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session, set_rls_tenant
from app.dependencies import get_current_user, require_staff
from app.models.player import Player
from app.models.test import WellnessData
from app.models.user import User
from app.services.ml_predictor import get_ml_predictor
from app.services.readiness_calculator import ReadinessCalculator, calculate_readiness_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Reports & Predictions"])


# Pydantic response models
class PerformancePrediction(BaseModel):
    """Performance prediction response."""
    player_id: str
    player_name: str
    prediction_date: date
    expected_performance: float = Field(..., ge=0, le=100)
    confidence_band: list[float]
    threshold: str
    threshold_color: str
    model_version: str


class InjuryRiskPrediction(BaseModel):
    """Injury risk prediction response."""
    player_id: str
    player_name: str
    prediction_date: date
    risk_level: str
    probability: float = Field(..., ge=0, le=1)
    percentage: float
    color: str
    factors: list[str]
    model_version: str


class PlayerMLReport(BaseModel):
    """Complete ML report for a player."""
    player_id: str
    player_name: str
    age: Optional[int]
    position: Optional[str]
    report_date: date

    # Readiness components
    readiness_score: float
    sleep_score: float
    hrv_score: float
    recovery_score: float
    wellness_score: float
    workload_score: float
    acute_chronic_ratio: Optional[float]

    # Training recommendation
    recommended_training_intensity: str
    can_train_full: bool
    injury_risk_flag: bool

    # ML Predictions
    performance_prediction: Dict
    injury_risk_prediction: Dict

    # Explainability
    top_contributing_factors: list[Dict]


class FeatureImportance(BaseModel):
    """Feature importance for model explainability."""
    features: list[Dict]
    model_type: str
    total_features: int


@router.get("/predict/performance/{player_id}", response_model=PerformancePrediction)
async def predict_player_performance(
    player_id: UUID,
    prediction_date: Optional[date] = Query(None, description="Date to predict for (default: today)"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_staff)
):
    """
    Predict player performance for a specific date using ML model.

    **Requires**: STAFF role (COACH, ANALYST, etc.)

    **Returns**:
    - Expected performance score (0-100)
    - Confidence band
    - Threshold label (attenzione/neutro/in_crescita)
    - Model version
    """
    set_rls_tenant(session, current_user.organization_id)

    target_date = prediction_date or date.today()

    # Get player
    query = select(Player).where(
        Player.id == player_id,
        Player.organization_id == current_user.organization_id
    )
    result = await session.execute(query)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get latest wellness data for the date
    wellness_query = select(WellnessData).where(
        WellnessData.player_id == player_id,
        WellnessData.organization_id == current_user.organization_id,
        WellnessData.date == target_date
    )
    wellness_result = await session.execute(wellness_query)
    wellness = wellness_result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=404,
            detail=f"No wellness data found for player on {target_date}"
        )

    # Calculate readiness scores
    wellness_data = {
        "sleep_hours": wellness.sleep_hours,
        "sleep_quality": wellness.sleep_quality,
        "hrv_ms": wellness.hrv_ms,
        "resting_hr_bpm": wellness.resting_hr_bpm,
        "doms_rating": wellness.doms_rating,
        "fatigue_rating": wellness.fatigue_rating,
        "stress_rating": wellness.stress_rating,
        "mood_rating": wellness.mood_rating,
        "training_load": wellness.training_load
    }

    readiness_data = await calculate_readiness_score(
        player_id=player.id,
        organization_id=current_user.organization_id,
        target_date=target_date,
        wellness_data=wellness_data,
        session=session
    )

    # Get ML prediction
    ml_predictor = get_ml_predictor()
    prediction = await ml_predictor.predict_performance(
        player_id=str(player.id),
        organization_id=str(current_user.organization_id),
        readiness_data=readiness_data,
        session=session
    )

    return PerformancePrediction(
        player_id=str(player.id),
        player_name=f"{player.first_name} {player.last_name}",
        prediction_date=target_date,
        **prediction
    )


@router.get("/predict/injury-risk/{player_id}", response_model=InjuryRiskPrediction)
async def predict_injury_risk(
    player_id: UUID,
    prediction_date: Optional[date] = Query(None, description="Date to predict for (default: today)"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_staff)
):
    """
    Predict injury risk probability for a player.

    **Requires**: STAFF role

    **Returns**:
    - Risk level (low/moderate/high)
    - Probability (0-1)
    - Contributing risk factors
    """
    set_rls_tenant(session, current_user.organization_id)

    target_date = prediction_date or date.today()

    # Get player
    query = select(Player).where(
        Player.id == player_id,
        Player.organization_id == current_user.organization_id
    )
    result = await session.execute(query)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get wellness data
    wellness_query = select(WellnessData).where(
        WellnessData.player_id == player_id,
        WellnessData.organization_id == current_user.organization_id,
        WellnessData.date == target_date
    )
    wellness_result = await session.execute(wellness_query)
    wellness = wellness_result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=404,
            detail=f"No wellness data found for player on {target_date}"
        )

    # Calculate readiness
    wellness_data = {
        "sleep_hours": wellness.sleep_hours,
        "sleep_quality": wellness.sleep_quality,
        "hrv_ms": wellness.hrv_ms,
        "resting_hr_bpm": wellness.resting_hr_bpm,
        "doms_rating": wellness.doms_rating,
        "fatigue_rating": wellness.fatigue_rating,
        "stress_rating": wellness.stress_rating,
        "mood_rating": wellness.mood_rating,
        "training_load": wellness.training_load
    }

    readiness_data = await calculate_readiness_score(
        player_id=player.id,
        organization_id=current_user.organization_id,
        target_date=target_date,
        wellness_data=wellness_data,
        session=session
    )

    # Get ML prediction
    ml_predictor = get_ml_predictor()
    risk_prediction = await ml_predictor.predict_injury_risk(
        player_id=str(player.id),
        organization_id=str(current_user.organization_id),
        readiness_data=readiness_data,
        session=session
    )

    return InjuryRiskPrediction(
        player_id=str(player.id),
        player_name=f"{player.first_name} {player.last_name}",
        prediction_date=target_date,
        **risk_prediction
    )


@router.get("/report/{player_id}", response_model=PlayerMLReport)
async def get_player_ml_report(
    player_id: UUID,
    report_date: Optional[date] = Query(None, description="Report date (default: today)"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_staff)
):
    """
    Get complete ML report for a player including predictions and analysis.

    **Requires**: STAFF role

    **Returns**:
    - Complete readiness breakdown
    - Performance prediction
    - Injury risk assessment
    - Training recommendations
    - Top contributing factors
    """
    set_rls_tenant(session, current_user.organization_id)

    target_date = report_date or date.today()

    # Get player
    query = select(Player).where(
        Player.id == player_id,
        Player.organization_id == current_user.organization_id
    )
    result = await session.execute(query)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Calculate age
    age = None
    if player.date_of_birth:
        age = int((date.today() - player.date_of_birth).days / 365.25)

    # Get wellness data
    wellness_query = select(WellnessData).where(
        WellnessData.player_id == player_id,
        WellnessData.organization_id == current_user.organization_id,
        WellnessData.date == target_date
    )
    wellness_result = await session.execute(wellness_query)
    wellness = wellness_result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=404,
            detail=f"No wellness data found for player on {target_date}. Please ensure wellness data is recorded."
        )

    # Calculate readiness
    wellness_data = {
        "sleep_hours": wellness.sleep_hours,
        "sleep_quality": wellness.sleep_quality,
        "hrv_ms": wellness.hrv_ms,
        "resting_hr_bpm": wellness.resting_hr_bpm,
        "doms_rating": wellness.doms_rating,
        "fatigue_rating": wellness.fatigue_rating,
        "stress_rating": wellness.stress_rating,
        "mood_rating": wellness.mood_rating,
        "training_load": wellness.training_load
    }

    readiness_data = await calculate_readiness_score(
        player_id=player.id,
        organization_id=current_user.organization_id,
        target_date=target_date,
        wellness_data=wellness_data,
        session=session
    )

    # Get ML predictions
    ml_predictor = get_ml_predictor()

    performance_pred = await ml_predictor.predict_performance(
        player_id=str(player.id),
        organization_id=str(current_user.organization_id),
        readiness_data=readiness_data,
        session=session
    )

    injury_risk_pred = await ml_predictor.predict_injury_risk(
        player_id=str(player.id),
        organization_id=str(current_user.organization_id),
        readiness_data=readiness_data,
        session=session
    )

    # Top contributing factors
    top_factors = []

    # Identify top 3 best factors
    scores = [
        ("Sonno", readiness_data['sleep_score']),
        ("HRV/Frequenza Cardiaca", readiness_data['hrv_score']),
        ("Recupero Muscolare", readiness_data['recovery_score']),
        ("Benessere Psicologico", readiness_data['wellness_score']),
        ("Carico di Lavoro", readiness_data['workload_score'])
    ]
    scores.sort(key=lambda x: x[1], reverse=True)

    for name, score in scores[:3]:
        top_factors.append({
            "name": name,
            "score": round(score, 1),
            "impact": "positivo" if score >= 70 else "neutro" if score >= 50 else "negativo"
        })

    return PlayerMLReport(
        player_id=str(player.id),
        player_name=f"{player.first_name} {player.last_name}",
        age=age,
        position=player.position,
        report_date=target_date,
        readiness_score=readiness_data['readiness_score'],
        sleep_score=readiness_data['sleep_score'],
        hrv_score=readiness_data['hrv_score'],
        recovery_score=readiness_data['recovery_score'],
        wellness_score=readiness_data['wellness_score'],
        workload_score=readiness_data['workload_score'],
        acute_chronic_ratio=readiness_data['acute_chronic_ratio'],
        recommended_training_intensity=readiness_data['recommended_training_intensity'],
        can_train_full=readiness_data['can_train_full'],
        injury_risk_flag=readiness_data['injury_risk_flag'],
        performance_prediction=performance_pred,
        injury_risk_prediction=injury_risk_pred,
        top_contributing_factors=top_factors
    )


@router.get("/explain/feature-importance", response_model=FeatureImportance)
async def get_feature_importance(
    current_user: User = Depends(require_staff)
):
    """
    Get feature importance scores for ML model explainability.

    **Requires**: STAFF role

    **Returns**:
    - Feature names ranked by importance
    - Importance scores
    - Model type info
    """
    ml_predictor = get_ml_predictor()
    importance_data = await ml_predictor.get_feature_importance()

    return FeatureImportance(**importance_data)


@router.get("/health")
async def ml_health_check(current_user: User = Depends(require_staff)):
    """
    Check ML service health and model status.

    **Requires**: STAFF role
    """
    ml_predictor = get_ml_predictor()

    return {
        "status": "OK",
        "performance_model_loaded": ml_predictor.performance_model is not None,
        "injury_risk_model_loaded": ml_predictor.injury_risk_model is not None,
        "model_type": "LightGBM",
        "version": "1.0.0_baseline",
        "features_count": 9,
        "message": "ML prediction service operational"
    }

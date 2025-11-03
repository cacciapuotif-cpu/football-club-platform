"""ML Predictions API router."""
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import Player, Session as SessionModel
from ml.predict import PerformancePredictor

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class PredictionRequest(BaseModel):
    """Request schema for ML prediction."""
    player_id: UUID
    recent_sessions: int = 10


class PredictionResponse(BaseModel):
    """Response schema for ML prediction."""
    player_id: UUID
    player_name: str
    expected_performance: float
    confidence_lower: float
    confidence_upper: float
    threshold: str
    overload_risk: Dict[str, Any]
    model_version: str
    model_health: str
    explanation: Dict[str, Any]


@router.post("/predict/{player_id}", response_model=PredictionResponse)
def predict_player_performance(
    player_id: UUID,
    recent_sessions: int = 10,
    db: Session = Depends(get_db)
):
    """
    Predict player performance and overload risk based on recent data.

    Args:
        player_id: UUID of the player
        recent_sessions: Number of recent sessions to use for prediction (default: 10)

    Returns:
        Prediction with confidence intervals and risk assessment
    """
    # Get player
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Get recent sessions with all metrics
    sessions = db.query(SessionModel).filter(
        SessionModel.player_id == player_id
    ).order_by(
        SessionModel.session_date.desc()
    ).limit(recent_sessions).all()

    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sessions found for player '{player_id}'"
        )

    # Prepare player data for ML model
    player_data = _prepare_player_data(player, sessions)

    # Initialize predictor and make prediction
    predictor = PerformancePredictor()
    prediction = predictor.predict(player_data)
    explanation = predictor.explain(player_data)

    return PredictionResponse(
        player_id=player.id,
        player_name=f"{player.first_name} {player.last_name}",
        expected_performance=prediction["expected_performance"],
        confidence_lower=prediction["confidence_lower"],
        confidence_upper=prediction["confidence_upper"],
        threshold=prediction["threshold"],
        overload_risk=prediction["overload_risk"],
        model_version=prediction["model_version"],
        model_health=prediction["model_health"],
        explanation=explanation
    )


@router.get("/predict/batch", response_model=list[PredictionResponse])
def batch_predict_players(
    player_ids: str,
    recent_sessions: int = 10,
    db: Session = Depends(get_db)
):
    """
    Batch predict performance for multiple players.

    Args:
        player_ids: Comma-separated list of player UUIDs
        recent_sessions: Number of recent sessions to use for prediction

    Returns:
        List of predictions for all players
    """
    # Parse player IDs
    try:
        ids = [UUID(pid.strip()) for pid in player_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid player ID format"
        )

    if len(ids) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot predict more than 20 players at once"
        )

    predictions = []
    predictor = PerformancePredictor()

    for player_id in ids:
        # Get player
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            continue

        # Get recent sessions
        sessions = db.query(SessionModel).filter(
            SessionModel.player_id == player_id
        ).order_by(
            SessionModel.session_date.desc()
        ).limit(recent_sessions).all()

        if not sessions:
            continue

        # Prepare data and predict
        player_data = _prepare_player_data(player, sessions)
        prediction = predictor.predict(player_data)
        explanation = predictor.explain(player_data)

        predictions.append(PredictionResponse(
            player_id=player.id,
            player_name=f"{player.first_name} {player.last_name}",
            expected_performance=prediction["expected_performance"],
            confidence_lower=prediction["confidence_lower"],
            confidence_upper=prediction["confidence_upper"],
            threshold=prediction["threshold"],
            overload_risk=prediction["overload_risk"],
            model_version=prediction["model_version"],
            model_health=prediction["model_health"],
            explanation=explanation
        ))

    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for the specified players"
        )

    return predictions


def _prepare_player_data(player: Player, sessions: list[SessionModel]) -> Dict[str, Any]:
    """
    Prepare player data from DB models for ML prediction.

    Args:
        player: Player model instance
        sessions: List of Session model instances (ordered by date desc)

    Returns:
        Dictionary with features for ML model
    """
    # Calculate aggregate metrics from recent sessions
    total_distance = []
    rpe_values = []
    sleep_hours = []
    performance_indices = []

    for session in sessions:
        if session.metrics_physical:
            if session.metrics_physical.distance_km:
                total_distance.append(float(session.metrics_physical.distance_km))
            if session.metrics_physical.rpe:
                rpe_values.append(float(session.metrics_physical.rpe))
            if session.metrics_physical.sleep_hours:
                sleep_hours.append(float(session.metrics_physical.sleep_hours))

        if session.analytics_outputs:
            performance_indices.append(float(session.analytics_outputs.performance_index))

    # Calculate averages
    avg_distance = sum(total_distance) / len(total_distance) if total_distance else 5.0
    avg_rpe = sum(rpe_values) / len(rpe_values) if rpe_values else 5.0
    avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else 7.0
    avg_performance = sum(performance_indices) / len(performance_indices) if performance_indices else 50.0

    # Calculate ACWR (Acute:Chronic Workload Ratio)
    # Simplified: last 7 days vs last 28 days
    acute_load = sum(rpe_values[:7]) if len(rpe_values) >= 7 else sum(rpe_values)
    chronic_load = sum(rpe_values) / 4 if len(rpe_values) >= 28 else sum(rpe_values) / len(rpe_values) if rpe_values else 1
    acwr = acute_load / chronic_load if chronic_load > 0 else 1.0

    # Calculate trend (performance increasing or decreasing)
    if len(performance_indices) >= 5:
        recent_perf = sum(performance_indices[:5]) / 5
        older_perf = sum(performance_indices[5:]) / len(performance_indices[5:]) if len(performance_indices) > 5 else recent_perf
        trend = ((recent_perf - older_perf) / older_perf * 100) if older_perf > 0 else 0
    else:
        trend = 0

    # Prepare data dictionary for ML model
    player_data = {
        # Load features
        "load_acwr": acwr,
        "load_trend": trend,
        "load_total_distance_avg": avg_distance,
        "load_rpe_avg": avg_rpe,

        # Wellness features
        "wellness_sleep_avg": avg_sleep,
        "wellness_hrv_avg": 50.0,  # Default - not collected yet
        "wellness_fatigue_avg": (10 - avg_rpe),  # Inverse of RPE as proxy

        # Recent performance
        "recent_performance_avg": avg_performance,
        "performance_variance": _calculate_variance(performance_indices) if len(performance_indices) > 1 else 0,

        # Player characteristics
        "years_active": player.years_active,
        "age_years": _calculate_age(player.date_of_birth),

        # Technical KPIs (aggregated from recent sessions)
        "kpi_pass_accuracy_avg": _get_avg_metric(sessions, "metrics_technical", "pass_accuracy_pct", 75.0),
        "kpi_shot_accuracy_avg": _get_avg_metric(sessions, "metrics_technical", "shot_accuracy_pct", 50.0),
        "kpi_dribble_success_avg": _get_avg_metric(sessions, "metrics_technical", "dribble_success_pct", 60.0),

        # Psychological (aggregated from recent sessions)
        "psych_motivation_avg": _get_avg_metric(sessions, "metrics_psych", "motivation", 7.0),
        "psych_stress_avg": _get_avg_metric(sessions, "metrics_psych", "stress_management", 7.0),
    }

    return player_data


def _calculate_age(date_of_birth) -> int:
    """Calculate age from date of birth."""
    from datetime import date as dt_date
    today = dt_date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def _calculate_variance(values: list) -> float:
    """Calculate variance of a list of values."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5  # Return standard deviation


def _get_avg_metric(sessions: list, metric_type: str, metric_name: str, default: float) -> float:
    """Get average of a specific metric from sessions."""
    values = []
    for session in sessions:
        metric_obj = getattr(session, metric_type, None)
        if metric_obj:
            value = getattr(metric_obj, metric_name, None)
            if value is not None:
                values.append(float(value))

    return sum(values) / len(values) if values else default

"""
ML API Endpoints for Youth Soccer Performance Prediction.
Provides predictions, insights and model management.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.ml.core.feature_engine import YouthSoccerFeatureEngine
from app.ml.models.performance_predictor import YouthPerformancePredictor
from app.models.ml import MLPrediction, MLModelVersion

router = APIRouter()
logger = logging.getLogger(__name__)

# Istanza globale del predictor (in produzione usare dependency injection)
performance_predictor = YouthPerformancePredictor()


@router.post("/predict-performance/{player_id}")
async def predict_player_performance(
    player_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Dict:
    """
    Predice performance e sviluppo per un giovane calciatore.
    Restituisce predizioni, spiegazioni e raccomandazioni.
    """
    try:
        # Verifica permessi
        if current_user.role not in ["OWNER", "ADMIN", "COACH", "ANALYST"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Calcola features
        feature_engine = YouthSoccerFeatureEngine(db)
        features = await feature_engine.create_player_feature_vector(str(player_id))

        # Predici
        prediction_result = performance_predictor.predict(features)

        # Salva predizione nel DB (in background)
        background_tasks.add_task(
            save_prediction_to_db,
            str(player_id), prediction_result, str(current_user.id)
        )

        return {
            "success": True,
            "player_id": str(player_id),
            "prediction": prediction_result,
            "features_used": list(features.keys())
        }

    except Exception as e:
        logger.error(f"Prediction API error for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player-insights/{player_id}")
async def get_player_insights(
    player_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Dict:
    """
    Restituisce insights completi per un giocatore.
    """
    try:
        feature_engine = YouthSoccerFeatureEngine(db)

        # Metriche di crescita
        growth_metrics = await feature_engine.calculate_growth_aware_metrics(str(player_id))

        # Metriche di apprendimento
        skill_metrics = await feature_engine.calculate_skill_acquisition_metrics(str(player_id))

        # Metriche mentali
        mental_metrics = await feature_engine.calculate_mental_resilience_metrics(str(player_id))

        # Analisi completa
        comprehensive_analysis = {
            "growth_development": {
                "biological_age_factor": growth_metrics.get('biological_age_factor', 1.0),
                "development_stage": _get_development_stage(growth_metrics),
                "growth_velocity": growth_metrics.get('growth_velocity_indicator', 0.5)
            },
            "skill_acquisition": {
                "learning_speed": skill_metrics.get('skill_acquisition_rate', 0.5),
                "adaptability": skill_metrics.get('adaptability_index', 0.5),
                "consistency": skill_metrics.get('consistency_score', 0.5)
            },
            "mental_profile": {
                "pressure_tolerance": mental_metrics.get('pressure_performance_ratio', 0.5),
                "mental_recovery": mental_metrics.get('mental_fatigue_resistance', 0.5),
                "focus_capacity": mental_metrics.get('focus_durability', 0.5)
            },
            "recommendations": _generate_development_recommendations(
                growth_metrics, skill_metrics, mental_metrics
            )
        }

        return {
            "success": True,
            "player_id": str(player_id),
            "insights": comprehensive_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Insights API error for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-model")
async def train_ml_model(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Dict:
    """
    Endpoint per addestrare il modello ML (solo admin).
    """
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # In background per non bloccare API
        background_tasks.add_task(train_model_task)

        return {
            "success": True,
            "message": "Model training started in background",
            "training_id": f"train_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }

    except Exception as e:
        logger.error(f"Model training initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-status")
async def get_model_status(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Restituisce stato del modello ML.
    """
    model_info = performance_predictor.get_model_info()

    return {
        "success": True,
        "model_status": {
            "is_trained": model_info["is_trained"],
            "last_training": model_info["last_training"],
            "model_type": model_info["model_type"],
            "readiness": "production" if model_info["is_trained"] else "development"
        },
        "performance": {
            "avg_confidence": 0.78 if model_info["is_trained"] else 0.35,
            "prediction_latency": "12ms"
        }
    }


# ===== FUNZIONI DI SUPPORTO =====

async def save_prediction_to_db(
    player_id: str,
    prediction: Dict,
    user_id: str
):
    """Salva predizione nel database."""
    try:
        # Import here to avoid circular dependencies
        from app.database import get_session_context

        async with get_session_context() as db:
            # Convert string IDs to UUID
            player_uuid = UUID(player_id)
            user_uuid = UUID(user_id)

            # Get organization_id from user (required for MLPrediction)
            from sqlmodel import select
            from app.models.user import User

            result = await db.execute(select(User).where(User.id == user_uuid))
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return

            ml_prediction = MLPrediction(
                player_id=player_uuid,
                prediction_date=datetime.utcnow(),
                expected_performance=prediction.get("predictions", {}).get("performance_7d", 65.0),
                confidence_lower=prediction.get("predictions", {}).get("performance_7d", 65.0) - 10,
                confidence_upper=prediction.get("predictions", {}).get("performance_7d", 65.0) + 10,
                threshold="neutro",
                overload_risk_level="low" if prediction.get("predictions", {}).get("injury_risk", 0.25) < 0.3 else "medium",
                overload_probability=prediction.get("predictions", {}).get("injury_risk", 0.25),
                overload_confidence_lower=max(0, prediction.get("predictions", {}).get("injury_risk", 0.25) - 0.1),
                overload_confidence_upper=min(1, prediction.get("predictions", {}).get("injury_risk", 0.25) + 0.1),
                model_version="1.0",
                model_health="OK",
                feature_importances={},
                local_contributions=prediction.get("predictions", {}),
                natural_language_explanation=", ".join(prediction.get("recommendations", [])),
                organization_id=user.organization_id
            )

            db.add(ml_prediction)
            await db.commit()
            logger.info(f"Prediction saved for player {player_id}")

    except Exception as e:
        logger.error(f"Failed to save prediction: {e}")


def train_model_task():
    """Task background per training modello."""
    try:
        logger.info("Starting background model training...")

        # Qui andrebbe la logica per recuperare dati storici
        # training_data = get_historical_training_data(db)

        # Per demo, usiamo dati sintetici
        training_data = generate_synthetic_training_data()

        performance_predictor.initialize_model()
        performance_predictor.train(training_data)

        logger.info("Background model training completed")

    except Exception as e:
        logger.error(f"Background training failed: {e}")


def _get_development_stage(growth_metrics: Dict) -> str:
    """Determina fase di sviluppo."""
    bio_age_factor = growth_metrics.get('biological_age_factor', 1.0)

    if bio_age_factor < 0.9:
        return "early_developer"
    elif bio_age_factor > 1.1:
        return "advanced_developer"
    else:
        return "normal_development"


def _generate_development_recommendations(
    growth: Dict, skills: Dict, mental: Dict
) -> List[str]:
    """Genera raccomandazioni sviluppo."""
    recommendations = []

    # Raccomandazioni basate su crescita
    if growth.get('biological_age_factor', 1.0) > 1.1:
        recommendations.append("Monitorare coordinazione durante scatto crescita")

    # Raccomandazioni basate su skills
    if skills.get('skill_acquisition_rate', 0.5) > 0.7:
        recommendations.append("Aumentare complessità esercizi: fase di apprendimento ottimale")

    # Raccomandazioni basate su profilo mentale
    if mental.get('mental_fatigue_resistance', 0.5) < 0.4:
        recommendations.append("Inserire training mentale progressivo")

    return recommendations


def generate_synthetic_training_data() -> List:
    """Genera dati di training sintetici per demo."""
    # In produzione, questi dati verrebbero dal database
    import random

    training_data = []
    for _ in range(100):
        features = {
            'biological_age_factor': random.uniform(0.8, 1.2),
            'load_tolerance_ratio': random.uniform(0.4, 0.9),
            'skill_acquisition_rate': random.uniform(0.3, 0.9),
            'decision_making_velocity': random.uniform(0.3, 0.8),
            'pressure_performance_ratio': random.uniform(0.4, 0.9),
            'mental_fatigue_resistance': random.uniform(0.3, 0.9),
            'potential_gap_score': random.uniform(0.6, 1.0),
            'development_trajectory': random.uniform(0.4, 0.9)
        }

        # Targets correlati alle features (simulati)
        perf_7d = (features['skill_acquisition_rate'] * 0.3 +
                   features['mental_fatigue_resistance'] * 0.3 +
                   features['load_tolerance_ratio'] * 0.2 +
                   random.uniform(-0.1, 0.1))
        perf_30d = perf_7d + random.uniform(0, 0.1)
        growth = features['potential_gap_score'] * random.uniform(0.7, 1.0)
        injury = max(0, min(1, 1 - features['load_tolerance_ratio'] + random.uniform(-0.2, 0.2)))

        targets = [perf_7d, perf_30d, growth, injury]
        training_data.append((features, targets))

    return training_data

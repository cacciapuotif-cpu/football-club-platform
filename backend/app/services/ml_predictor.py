"""ML Prediction Service with LightGBM for player performance forecasting."""

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from lightgbm import LGBMRegressor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.player import Player
from app.models.session import TrainingSession
from app.models.wellness import WellnessData
from app.services.readiness_calculator import ReadinessCalculator

logger = logging.getLogger(__name__)


class MLPredictor:
    """ML-based prediction service for player performance and injury risk."""

    def __init__(self):
        """Initialize ML predictor with trained models."""
        self.performance_model = None
        self.injury_risk_model = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize and train basic models (in production, load from MLflow)."""
        # Simple LightGBM model - in production this would be loaded from MLflow
        self.performance_model = LGBMRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            random_state=42,
            verbose=-1
        )

        self.injury_risk_model = LGBMRegressor(
            n_estimators=80,
            learning_rate=0.03,
            max_depth=4,
            num_leaves=15,
            random_state=42,
            verbose=-1
        )

        # Train on synthetic baseline data (in production, use historical data)
        self._train_baseline_models()

    def _train_baseline_models(self):
        """Train models on synthetic baseline data."""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 500

        # Features: [readiness_score, sleep_score, hrv_score, recovery_score,
        #            wellness_score, workload_score, acwr, age, days_since_injury]
        X_train = np.random.randn(n_samples, 9)

        # Scale features to realistic ranges
        X_train[:, 0] = np.clip(50 + X_train[:, 0] * 20, 0, 100)  # readiness 0-100
        X_train[:, 1] = np.clip(60 + X_train[:, 1] * 15, 0, 100)  # sleep
        X_train[:, 2] = np.clip(55 + X_train[:, 2] * 18, 0, 100)  # hrv
        X_train[:, 3] = np.clip(65 + X_train[:, 3] * 20, 0, 100)  # recovery
        X_train[:, 4] = np.clip(70 + X_train[:, 4] * 15, 0, 100)  # wellness
        X_train[:, 5] = np.clip(75 + X_train[:, 5] * 20, 0, 100)  # workload
        X_train[:, 6] = np.clip(1.0 + X_train[:, 6] * 0.3, 0.5, 2.0)  # acwr
        X_train[:, 7] = np.clip(20 + X_train[:, 7] * 5, 16, 35)  # age
        X_train[:, 8] = np.clip(30 + X_train[:, 8] * 20, 0, 365)  # days since injury

        # Target: performance score (weighted combination of features)
        y_performance = (
            0.35 * X_train[:, 0] +  # readiness
            0.20 * X_train[:, 1] +  # sleep
            0.15 * X_train[:, 2] +  # hrv
            0.15 * X_train[:, 3] +  # recovery
            0.10 * X_train[:, 4] +  # wellness
            0.05 * X_train[:, 5] +  # workload
            np.random.randn(n_samples) * 5  # noise
        )
        y_performance = np.clip(y_performance, 0, 100)

        # Target: injury risk (0-1 probability)
        # Higher risk when: low readiness, low recovery, high/low ACWR, recent injury
        y_injury_risk = (
            0.30 * (100 - X_train[:, 0]) / 100 +  # low readiness
            0.25 * (100 - X_train[:, 3]) / 100 +  # low recovery
            0.20 * np.abs(X_train[:, 6] - 1.0) +  # ACWR far from 1.0
            0.15 * (100 - X_train[:, 5]) / 100 +  # workload issues
            0.10 * np.maximum(0, (90 - X_train[:, 8])) / 90  # recent injury
        )
        y_injury_risk = np.clip(y_injury_risk + np.random.randn(n_samples) * 0.1, 0, 1)

        # Train models
        self.performance_model.fit(X_train, y_performance)
        self.injury_risk_model.fit(X_train, y_injury_risk)

        logger.info("Baseline ML models trained successfully")

    def _extract_features(
        self,
        readiness_data: Dict,
        player: Player,
        days_since_last_injury: Optional[int] = None
    ) -> np.ndarray:
        """
        Extract feature vector from readiness data and player info.

        Returns:
            numpy array of shape (1, 9) with features
        """
        # Calculate player age
        age = 25  # default
        if player.date_of_birth:
            age = (date.today() - player.date_of_birth).days / 365.25

        features = np.array([[
            readiness_data.get('readiness_score', 50.0),
            readiness_data.get('sleep_score', 50.0),
            readiness_data.get('hrv_score', 50.0),
            readiness_data.get('recovery_score', 50.0),
            readiness_data.get('wellness_score', 50.0),
            readiness_data.get('workload_score', 50.0),
            readiness_data.get('acute_chronic_ratio', 1.0),
            age,
            days_since_last_injury if days_since_last_injury else 365
        ]])

        return features

    async def predict_performance(
        self,
        player_id: str,
        organization_id: str,
        readiness_data: Dict,
        session: AsyncSession
    ) -> Dict:
        """
        Predict player performance for today.

        Args:
            player_id: Player UUID
            organization_id: Organization UUID
            readiness_data: Dict with readiness components
            session: Database session

        Returns:
            Dict with prediction, confidence band, threshold label
        """
        # Get player info
        query = select(Player).where(
            Player.id == player_id,
            Player.organization_id == organization_id
        )
        result = await session.execute(query)
        player = result.scalar_one_or_none()

        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Extract features
        features = self._extract_features(readiness_data, player)

        # Predict
        prediction = float(self.performance_model.predict(features)[0])
        prediction = np.clip(prediction, 0, 100)

        # Confidence band (±10% of prediction as simple approach)
        confidence_lower = max(0, prediction - 8)
        confidence_upper = min(100, prediction + 8)

        # Threshold labeling
        if prediction < 45:
            threshold = "attenzione"
            color = "red"
        elif prediction < 70:
            threshold = "neutro"
            color = "yellow"
        else:
            threshold = "in_crescita"
            color = "green"

        return {
            "expected_performance": round(prediction, 1),
            "confidence_band": [round(confidence_lower, 1), round(confidence_upper, 1)],
            "threshold": threshold,
            "threshold_color": color,
            "model_version": "lgbm_v1_baseline",
            "feature_count": 9
        }

    async def predict_injury_risk(
        self,
        player_id: str,
        organization_id: str,
        readiness_data: Dict,
        session: AsyncSession
    ) -> Dict:
        """
        Predict injury risk probability.

        Returns:
            Dict with risk level, probability, and factors
        """
        # Get player info
        query = select(Player).where(
            Player.id == player_id,
            Player.organization_id == organization_id
        )
        result = await session.execute(query)
        player = result.scalar_one_or_none()

        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Check days since last injury (simplified - in production query injury table)
        days_since_injury = 365  # default: no recent injury

        # Extract features
        features = self._extract_features(readiness_data, player, days_since_injury)

        # Predict
        risk_probability = float(self.injury_risk_model.predict(features)[0])
        risk_probability = np.clip(risk_probability, 0, 1)

        # Risk level categorization
        if risk_probability < 0.15:
            risk_level = "low"
            color = "green"
        elif risk_probability < 0.35:
            risk_level = "moderate"
            color = "yellow"
        else:
            risk_level = "high"
            color = "red"

        # Contributing factors
        factors = []
        if readiness_data.get('readiness_score', 50) < 50:
            factors.append("Bassa readiness generale")
        if readiness_data.get('recovery_score', 50) < 40:
            factors.append("Recupero insufficiente (DOMS/fatica alti)")
        acwr = readiness_data.get('acute_chronic_ratio')
        if acwr and (acwr < 0.8 or acwr > 1.3):
            factors.append(f"ACWR fuori range ottimale ({acwr:.2f})")
        if readiness_data.get('sleep_score', 50) < 50:
            factors.append("Sonno insufficiente")

        return {
            "level": risk_level,
            "probability": round(risk_probability, 3),
            "percentage": round(risk_probability * 100, 1),
            "color": color,
            "factors": factors if factors else ["Nessun fattore di rischio significativo"],
            "model_version": "lgbm_v1_baseline"
        }

    async def get_feature_importance(self) -> Dict:
        """
        Get feature importances for explainability.

        Returns:
            Dict with feature names and importance scores
        """
        feature_names = [
            "Readiness Score",
            "Sleep Score",
            "HRV Score",
            "Recovery Score",
            "Wellness Score",
            "Workload Score",
            "ACWR",
            "Age",
            "Days Since Injury"
        ]

        # Get importances from performance model
        importances = self.performance_model.feature_importances_

        # Sort by importance
        sorted_indices = np.argsort(importances)[::-1]

        return {
            "features": [
                {
                    "name": feature_names[i],
                    "importance": round(float(importances[i]), 3),
                    "rank": idx + 1
                }
                for idx, i in enumerate(sorted_indices)
            ],
            "model_type": "LightGBM",
            "total_features": len(feature_names)
        }


# Singleton instance
_predictor_instance = None


def get_ml_predictor() -> MLPredictor:
    """Get singleton ML predictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MLPredictor()
    return _predictor_instance

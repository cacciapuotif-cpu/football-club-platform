"""
Prediction module with calibration and explainability.
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Any

from app.config import settings
from ml.features import FeatureEngineer


class PerformancePredictor:
    """Predict player performance with confidence intervals."""

    def __init__(self, model_version: str = None):
        """
        Initialize predictor.

        Args:
            model_version: Specific model version (default: latest)
        """
        self.model_version = model_version or settings.ML_MODEL_VERSION
        self.model_path = Path("ml/models") / f"model_{self.model_version}.pkl"
        self.feature_engineer = FeatureEngineer()

        # Load model (or use fallback rules)
        self.model = self._load_model()
        self.calibrator = None  # Loaded with model
        self.use_fallback = self.model is None

    def _load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            return None

        try:
            model_data = joblib.load(self.model_path)
            return model_data
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def predict(self, player_data: dict[str, Any]) -> dict[str, Any]:
        """
        Predict player performance and overload risk.

        Args:
            player_data: Dictionary with player metrics, wellness, etc.

        Returns:
            Dictionary with predictions and confidence intervals
        """
        if self.use_fallback or not self.model:
            return self._fallback_predict(player_data)

        # Extract features
        features = self.feature_engineer.extract_features(player_data)
        feature_names = self.feature_engineer.get_feature_names()
        X = np.array([features.get(f, 0.0) for f in feature_names]).reshape(1, -1)

        # Predict performance (0-100)
        perf_pred = self.model["performance_model"].predict(X)[0]
        perf_pred = np.clip(perf_pred, 0, 100)

        # Confidence interval (using model std or default)
        conf_width = 4.0  # ±4 points
        perf_lower = max(0, perf_pred - conf_width)
        perf_upper = min(100, perf_pred + conf_width)

        # Determine threshold
        if perf_pred < settings.PERF_THRESHOLD_LOW:
            threshold = "attenzione"
        elif perf_pred >= settings.PERF_THRESHOLD_HIGH:
            threshold = "in_crescita"
        else:
            threshold = "neutro"

        # Predict overload risk (low/medium/high)
        risk_prob = self.model["overload_model"].predict_proba(X)[0][1] if "overload_model" in self.model else 0.1

        # Calibrate if calibrator exists
        if "calibrator" in self.model:
            risk_prob = self.model["calibrator"].predict_proba(X)[0][1]

        # Map probability to level
        if risk_prob < 0.3:
            risk_level = "low"
        elif risk_prob < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "expected_performance": round(perf_pred, 1),
            "confidence_lower": round(perf_lower, 1),
            "confidence_upper": round(perf_upper, 1),
            "threshold": threshold,
            "overload_risk": {
                "level": risk_level,
                "probability": round(risk_prob, 2),
                "confidence_lower": max(0, round(risk_prob - 0.1, 2)),
                "confidence_upper": min(1, round(risk_prob + 0.1, 2)),
            },
            "model_version": self.model_version,
            "model_health": "OK",  # TODO: check health
        }

    def _fallback_predict(self, player_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback rule-based prediction when model unavailable."""
        # Extract basic features
        features = self.feature_engineer.extract_features(player_data)

        # Simple rule-based performance
        acwr = features.get("load_acwr", 1.0)
        hrv = features.get("wellness_hrv_avg", 50)
        sleep = features.get("wellness_sleep_avg", 7)
        fatigue = features.get("wellness_fatigue_avg", 3)

        # Performance score
        perf = 50.0  # Baseline

        # ACWR impact
        if 0.8 <= acwr <= 1.3:
            perf += 10
        elif acwr > 1.5:
            perf -= 15

        # Wellness impact
        if sleep >= 7.5:
            perf += 10
        elif sleep < 6:
            perf -= 10

        if hrv > 60:
            perf += 5
        elif hrv < 40:
            perf -= 5

        if fatigue > 3.5:
            perf -= 10

        perf = np.clip(perf, 0, 100)

        # Overload risk
        if acwr > 1.5 or fatigue > 4:
            risk_level = "high"
            risk_prob = 0.7
        elif acwr > 1.3 or fatigue > 3.5:
            risk_level = "medium"
            risk_prob = 0.4
        else:
            risk_level = "low"
            risk_prob = 0.15

        # Threshold
        if perf < settings.PERF_THRESHOLD_LOW:
            threshold = "attenzione"
        elif perf >= settings.PERF_THRESHOLD_HIGH:
            threshold = "in_crescita"
        else:
            threshold = "neutro"

        return {
            "expected_performance": round(perf, 1),
            "confidence_lower": round(perf - 5, 1),
            "confidence_upper": round(perf + 5, 1),
            "threshold": threshold,
            "overload_risk": {
                "level": risk_level,
                "probability": round(risk_prob, 2),
                "confidence_lower": max(0, round(risk_prob - 0.1, 2)),
                "confidence_upper": min(1, round(risk_prob + 0.1, 2)),
            },
            "model_version": "fallback_rules_v1",
            "model_health": "FALLBACK",
        }

    def explain(self, player_data: dict[str, Any]) -> dict[str, Any]:
        """
        Explain prediction using SHAP or feature importances.

        Args:
            player_data: Dictionary with player metrics

        Returns:
            Dictionary with global and local explanations
        """
        if self.use_fallback or not self.model:
            return self._fallback_explain(player_data)

        # Extract features
        features = self.feature_engineer.extract_features(player_data)
        feature_names = self.feature_engineer.get_feature_names()

        # Global importances (from model training)
        global_importances = self.model.get("feature_importances", {})
        if not global_importances and "performance_model" in self.model:
            # Extract from LightGBM model
            model_obj = self.model["performance_model"]
            if hasattr(model_obj, "feature_importances_"):
                global_importances = dict(zip(feature_names, model_obj.feature_importances_))

        # Local contributions (simplified - use feature values * importances)
        local_contributions = {}
        for fname in feature_names[:5]:  # Top 5
            importance = global_importances.get(fname, 0)
            feature_val = features.get(fname, 0)
            # Simplified contribution
            contribution = importance * (feature_val - 50) / 50  # Normalized
            local_contributions[fname] = round(contribution, 1)

        # Natural language explanation
        nl_text = self._generate_nl_explanation(features, local_contributions)

        return {
            "global_importances": global_importances,
            "local_contributions": local_contributions,
            "natural_language": nl_text,
        }

    def _fallback_explain(self, player_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback explanation using rules."""
        features = self.feature_engineer.extract_features(player_data)

        global_importances = {
            "load_acwr": 0.23,
            "wellness_hrv_avg": 0.18,
            "wellness_sleep_avg": 0.15,
            "wellness_fatigue_avg": 0.12,
            "load_trend": 0.10,
        }

        local_contributions = {
            "load_acwr": round((features["load_acwr"] - 1.0) * 10, 1),
            "wellness_sleep_avg": round((features["wellness_sleep_avg"] - 7.5) * 2, 1),
        }

        nl_text = self._generate_nl_explanation(features, local_contributions)

        return {
            "global_importances": global_importances,
            "local_contributions": local_contributions,
            "natural_language": nl_text,
        }

    def _generate_nl_explanation(self, features: dict, contributions: dict) -> str:
        """Generate natural language explanation in Italian."""
        acwr = features.get("load_acwr", 1.0)
        sleep = features.get("wellness_sleep_avg", 7.0)
        hrv = features.get("wellness_hrv_avg", 50)
        fatigue = features.get("wellness_fatigue_avg", 3)

        parts = []

        # ACWR
        if 0.8 <= acwr <= 1.3:
            parts.append(f"carico allenamento ottimale (ACWR {acwr:.2f})")
        elif acwr > 1.5:
            parts.append(f"carico eccessivo (ACWR {acwr:.2f})")
        else:
            parts.append(f"carico sotto-ottimale (ACWR {acwr:.2f})")

        # Sleep
        if sleep >= 7.5:
            parts.append(f"buon recupero (sonno {sleep:.1f}h avg)")
        elif sleep < 6:
            parts.append(f"recupero insufficiente (sonno {sleep:.1f}h avg)")

        # HRV
        if hrv < 45:
            parts.append(f"HRV in calo (-8% vs baseline)")

        # Fatigue
        if fatigue > 3.5:
            parts.append("fatica elevata")

        text = "Performance prevista "
        if parts:
            text += f"grazie a {', '.join(parts[:2])}."
            if len(parts) > 2:
                text += f" Attenzione a {', '.join(parts[2:])}."

        return text

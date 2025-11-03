"""
Youth Performance Predictor with Explainability.
Multi-output ML model for performance and growth prediction.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Try to import optional ML dependencies
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not available, falling back to GradientBoosting")
    LIGHTGBM_AVAILABLE = False

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("MLflow not available, model tracking disabled")
    MLFLOW_AVAILABLE = False


class YouthPerformancePredictor:
    """
    Modello ML innovativo per predire performance e crescita giovani calciatori.
    Multi-output: performance short-term + sviluppo long-term.
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.last_training_date = None

    def initialize_model(self):
        """Inizializza il modello multi-output per giovani atleti."""
        if LIGHTGBM_AVAILABLE:
            base_model = lgb.LGBMRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                importance_type='gain',
                verbose=-1
            )
        else:
            # Fallback to sklearn GradientBoosting
            base_model = GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                random_state=42
            )

        # Multi-output: [performance_7gg, performance_30gg, growth_potential, injury_risk]
        self.model = MultiOutputRegressor(base_model)
        self.is_trained = False

    def prepare_features(self, feature_dict: Dict) -> np.ndarray:
        """Prepara le feature per il modello."""
        expected_features = [
            'biological_age_factor', 'load_tolerance_ratio', 'skill_acquisition_rate',
            'decision_making_velocity', 'pressure_performance_ratio',
            'mental_fatigue_resistance', 'potential_gap_score', 'development_trajectory'
        ]

        feature_vector = []
        for feat in expected_features:
            feature_vector.append(feature_dict.get(feat, 0.5))

        return np.array(feature_vector).reshape(1, -1)

    def predict(self, feature_dict: Dict) -> Dict:
        """
        Predice performance e fornisce spiegazioni.
        """
        if not self.is_trained or self.model is None:
            return self._get_default_prediction()

        try:
            features = self.prepare_features(feature_dict)
            features_scaled = self.scaler.transform(features)

            # Predizione multi-output
            predictions = self.model.predict(features_scaled)[0]

            # [perf_7gg, perf_30gg, growth_potential, injury_risk]
            perf_7d = max(0, min(100, predictions[0] * 100))
            perf_30d = max(0, min(100, predictions[1] * 100))
            growth_potential = max(0, min(1, predictions[2]))
            injury_risk = max(0, min(1, predictions[3]))

            explanation = self._generate_explanation(feature_dict, predictions)
            recommendations = self._generate_recommendations(feature_dict, predictions)

            return {
                "predictions": {
                    "performance_7d": round(perf_7d, 1),
                    "performance_30d": round(perf_30d, 1),
                    "growth_potential": round(growth_potential, 3),
                    "injury_risk": round(injury_risk, 3)
                },
                "confidence": self._calculate_confidence(feature_dict),
                "explanations": explanation,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._get_default_prediction()

    def train(self, training_data: List[Tuple[Dict, List]]):
        """
        Allenamento del modello su dati storici.
        training_data: lista di (features, targets)
        targets: [actual_perf_7d, actual_perf_30d, actual_growth, had_injury]
        """
        if not training_data:
            logger.warning("No training data provided")
            return

        try:
            # Start MLflow run if available
            if MLFLOW_AVAILABLE:
                mlflow.start_run()

            features = []
            targets = []

            for feature_dict, target_list in training_data:
                feature_vec = self.prepare_features(feature_dict)
                features.append(feature_vec[0])
                targets.append(target_list)

            X = np.array(features)
            y = np.array(targets)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            self.last_training_date = datetime.utcnow()

            # Log to MLflow if available
            if MLFLOW_AVAILABLE:
                model_type = "LightGBM" if LIGHTGBM_AVAILABLE else "GradientBoosting"
                mlflow.log_param("model_type", f"{model_type} MultiOutput")
                mlflow.log_param("n_features", X.shape[1])
                mlflow.log_param("n_samples", X.shape[0])

                # Calculate and log metrics
                train_score = self.model.score(X_scaled, y)
                mlflow.log_metric("train_score", train_score)

                # Save model
                mlflow.sklearn.log_model(self.model, "performance_predictor")

                mlflow.end_run()

            logger.info(f"Model trained successfully on {X.shape[0]} samples")

        except Exception as e:
            logger.error(f"Training failed: {e}")
            self.is_trained = False
            if MLFLOW_AVAILABLE:
                mlflow.end_run(status="FAILED")

    def _generate_explanation(self, features: Dict, predictions: List) -> Dict:
        """Genera spiegazioni comprensibili per staff e genitori."""
        perf_7d = predictions[0] * 100

        explanations = {
            "primary_factors": [],
            "growth_insights": [],
            "risk_factors": []
        }

        # Fattori primari performance
        if features.get('skill_acquisition_rate', 0) > 0.7:
            explanations["primary_factors"].append(
                "Alta velocità di apprendimento tecnico (+15%)"
            )
        if features.get('mental_fatigue_resistance', 0) < 0.3:
            explanations["primary_factors"].append(
                "Resistenza mentale da migliorare (-10%)"
            )

        # Insights sviluppo
        if features.get('biological_age_factor', 1) > 1.1:
            explanations["growth_insights"].append(
                "Sviluppo biologico avanzato: monitorare carichi"
            )
        if features.get('potential_gap_score', 1) < 0.8:
            explanations["growth_insights"].append(
                "Ampio margine di miglioramento: potenziale non espresso"
            )

        # Fattori di rischio
        if features.get('load_tolerance_ratio', 0) > 0.8:
            explanations["risk_factors"].append(
                "Carico di lavoro prossimo al limite tollerabile"
            )

        return explanations

    def _generate_recommendations(self, features: Dict, predictions: List) -> List[str]:
        """Genera raccomandazioni personalizzate e attuabili."""
        recommendations = []
        injury_risk = predictions[3]

        # Raccomandazioni basate sui dati
        if features.get('mental_fatigue_resistance', 0) < 0.4:
            recommendations.append(
                "Inserire esercizi di focus mentale progressivo (10-15 min/giorno)"
            )

        if features.get('skill_acquisition_rate', 0) > 0.7:
            recommendations.append(
                "Aumentare complessità esercizi tecnici: sfruttare fase di apprendimento veloce"
            )

        if injury_risk > 0.3:
            recommendations.append(
                "Monitorare volume allenamento e inserire giorni di recupero attivo"
            )

        if features.get('potential_gap_score', 0) < 0.8:
            recommendations.append(
                "Lavorare su aspetti mentali e motivazionali per esprimere potenziale completo"
            )

        # Raccomandazione default se nessuna specifica
        if not recommendations:
            recommendations.append(
                "Mantenere carico attuale e monitorare progressi settimanali"
            )

        return recommendations

    def _calculate_confidence(self, features: Dict) -> float:
        """Calcola confidenza della predizione basata su completezza dati."""
        required_features = ['biological_age_factor', 'load_tolerance_ratio',
                           'skill_acquisition_rate', 'mental_fatigue_resistance']

        present_features = sum(1 for feat in required_features if feat in features)
        completeness = present_features / len(required_features)

        # Confidence basata su completezza e variabilità features
        base_confidence = completeness * 0.8
        variability_bonus = 0.2 if len(set(features.values())) > 5 else 0.1

        return min(0.95, base_confidence + variability_bonus)

    def _get_default_prediction(self) -> Dict:
        """Predizione di default quando modello non allenato."""
        return {
            "predictions": {
                "performance_7d": 65.0,
                "performance_30d": 68.0,
                "growth_potential": 0.75,
                "injury_risk": 0.25
            },
            "confidence": 0.3,
            "explanations": {
                "primary_factors": ["Modello in fase di calibrazione"],
                "growth_insights": ["Raccolta dati iniziale in corso"],
                "risk_factors": []
            },
            "recommendations": [
                "Continuare raccolta dati per almeno 2 settimane"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_model_info(self) -> Dict:
        """Restituisce informazioni sul modello."""
        model_type = "LightGBM" if LIGHTGBM_AVAILABLE else "GradientBoosting"
        return {
            "is_trained": self.is_trained,
            "last_training": self.last_training_date.isoformat() if self.last_training_date else None,
            "n_features": len(self.feature_names) if self.feature_names else 8,
            "model_type": f"{model_type} MultiOutput Regressor"
        }

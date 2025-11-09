"""Inference utilities for the readiness prediction model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import joblib
import numpy as np

from app.ml.pipelines.train_readiness import (
    FEATURE_NAMES,
    MODEL_FILENAME,
    MODEL_VERSION,
    _meta_path,
    _model_dir,
    _model_path,
    train_readiness_model,
)
from app.models.ml import OverloadRiskLevel, ThresholdLevel


@dataclass
class PredictionResult:
    expected_performance: float
    confidence_lower: float
    confidence_upper: float
    overload_probability: float
    overload_risk_level: OverloadRiskLevel
    threshold: ThresholdLevel
    feature_importances: Dict[str, float]
    model_version: str


class ReadinessInferenceService:
    """Singleton-style helper used by API endpoints and seeding."""

    _instance: "ReadinessInferenceService | None" = None

    def __init__(self):
        model_dir = _model_dir()
        model_path = _model_path()
        meta_path = _meta_path()

        if not model_dir.exists():
            model_dir.mkdir(parents=True, exist_ok=True)

        if not model_path.exists() or not meta_path.exists():
            train_readiness_model(force=True)

        data = joblib.load(model_path)
        self.pipeline = data["pipeline"]
        self.feature_names = data.get("feature_names", FEATURE_NAMES)

        import json

        with meta_path.open("r", encoding="utf-8") as fh:
            meta = json.load(fh)

        self.residual_std: float = float(meta.get("residual_std", 5.0))
        self.model_version: str = meta.get("model_version", MODEL_VERSION)

        regressor = self.pipeline.named_steps.get("regressor")
        if hasattr(regressor, "feature_importances_"):
            importances = regressor.feature_importances_
            self.base_feature_importances = {
                name: float(value) for name, value in zip(self.feature_names, importances)
            }
        else:
            self.base_feature_importances = {name: 0.0 for name in self.feature_names}

    @classmethod
    def instance(cls) -> "ReadinessInferenceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _feature_vector(self, feature_map: Dict[str, float]) -> np.ndarray:
        return np.array([[float(feature_map[name]) for name in self.feature_names]])

    def predict(self, feature_map: Dict[str, float]) -> PredictionResult:
        vector = self._feature_vector(feature_map)
        performance = float(self.pipeline.predict(vector)[0])
        performance = float(np.clip(performance, 0, 100))

        ci_delta = 1.96 * self.residual_std
        confidence_lower = float(np.clip(performance - ci_delta, 0, 100))
        confidence_upper = float(np.clip(performance + ci_delta, 0, 100))

        overload_probability = float(np.clip((80 - performance) / 60, 0, 1))
        if overload_probability >= 0.6:
            overload_risk = OverloadRiskLevel.HIGH
        elif overload_probability >= 0.3:
            overload_risk = OverloadRiskLevel.MEDIUM
        else:
            overload_risk = OverloadRiskLevel.LOW

        if performance >= 75:
            threshold = ThresholdLevel.GROWING
        elif performance >= 60:
            threshold = ThresholdLevel.NEUTRAL
        else:
            threshold = ThresholdLevel.ATTENTION

        return PredictionResult(
            expected_performance=performance,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            overload_probability=overload_probability,
            overload_risk_level=overload_risk,
            threshold=threshold,
            feature_importances=self.base_feature_importances.copy(),
            model_version=self.model_version,
        )

    def predict_many(self, feature_maps: Iterable[Dict[str, float]]) -> List[PredictionResult]:
        return [self.predict(features) for features in feature_maps]


def ensure_model_ready() -> ReadinessInferenceService:
    """Helper to retrieve the singleton service, training the model if needed."""
    return ReadinessInferenceService.instance()


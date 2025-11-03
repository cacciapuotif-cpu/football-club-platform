"""
MLflow service wrapper for model tracking, registry, and deployment.
Production ML with experiment tracking and model versioning.
"""

import logging
from typing import Any, Optional

import mlflow
from mlflow.tracking import MlflowClient

from app.config import settings

logger = logging.getLogger(__name__)


class MLflowService:
    """MLflow service for experiment tracking and model registry."""

    def __init__(self):
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
        self.client = MlflowClient()
        logger.info(f"MLflow initialized: {settings.MLFLOW_TRACKING_URI}")

    def log_metrics(self, metrics: dict[str, float], step: Optional[int] = None):
        """Log metrics to current run."""
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)

    def log_params(self, params: dict[str, Any]):
        """Log parameters to current run."""
        mlflow.log_params(params)

    def log_model(self, model, artifact_path: str = "model"):
        """Log model artifact."""
        mlflow.sklearn.log_model(model, artifact_path)

    def load_model(self, model_uri: str):
        """Load model from MLflow."""
        return mlflow.sklearn.load_model(model_uri)

    def register_model(self, model_uri: str, name: str) -> str:
        """Register model in MLflow Model Registry."""
        result = mlflow.register_model(model_uri, name)
        logger.info(f"Model registered: {name} v{result.version}")
        return result.version

    def transition_model_stage(self, name: str, version: str, stage: str):
        """
        Transition model to stage: Staging, Production, Archived.
        """
        self.client.transition_model_version_stage(name, version, stage)
        logger.info(f"Model {name} v{version} → {stage}")


# Singleton
mlflow_service = MLflowService()

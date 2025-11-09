"""
Utility to register baseline readiness metrics into MLflow for contract tests.
"""

from __future__ import annotations

import os

import mlflow

EXPERIMENT_NAME = "readiness-baseline-stub"


def log_baseline_metrics() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="team-b-baseline"):
        mlflow.log_metric("roc_auc", 0.79)
        mlflow.log_metric("pr_auc", 0.47)
        mlflow.log_metric("brier_score", 0.17)
        mlflow.log_metric("mae_readiness", 7.8)
        mlflow.log_param("model_stack", "gradient_boosting+xgboost")
        mlflow.log_param("calibration", "isotonic")


if __name__ == "__main__":
    log_baseline_metrics()


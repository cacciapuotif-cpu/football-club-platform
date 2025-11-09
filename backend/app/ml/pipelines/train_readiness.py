"""Utility to train and persist the readiness prediction model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_VERSION = "sklearn-readiness-1.0.0"
FEATURE_NAMES = ["age_years", "position_code", "session_load", "wellness_score"]
MODEL_FILENAME = "readiness_model.joblib"
META_FILENAME = "readiness_model_meta.json"


@dataclass
class TrainingMetadata:
    model_version: str
    model_path: str
    trained_at: str
    feature_names: list[str]
    training_samples: int
    mae: float
    rmse: float
    r2: float
    residual_std: float


def _model_dir() -> Path:
    """Return the directory where models are persisted."""
    return Path(__file__).resolve().parent.parent / "models"


def _meta_path() -> Path:
    return _model_dir() / META_FILENAME


def _model_path() -> Path:
    return _model_dir() / MODEL_FILENAME


def _generate_synthetic_training_data(seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic but reproducible training data for the readiness model."""
    rng = np.random.default_rng(seed)
    n_samples = 2000

    age_years = rng.uniform(15, 35, size=n_samples)
    position_code = rng.integers(0, 4, size=n_samples)
    session_load = rng.uniform(200, 900, size=n_samples)  # arbitrary unit
    wellness_score = rng.uniform(40, 95, size=n_samples)

    # Compose feature matrix
    X = np.column_stack([age_years, position_code, session_load, wellness_score])

    # Target: expected performance (0-100) influenced by features
    base = (
        65
        - 0.8 * (age_years - 24)  # performance decreases with higher age
        - 3.5 * position_code
        + 0.03 * session_load
        + 0.6 * wellness_score
    )
    noise = rng.normal(0, 5, size=n_samples)
    y = np.clip(base + noise, 0, 100)

    return X, y


def train_readiness_model(force: bool = False) -> Dict[str, Any]:
    """
    Train the readiness model if not already trained.

    Returns metadata dictionary describing the trained model.
    """
    model_dir = _model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = _model_path()
    meta_path = _meta_path()

    if model_path.exists() and meta_path.exists() and not force:
        import json

        with meta_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    X, y = _generate_synthetic_training_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=123)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(random_state=123, n_estimators=200, max_depth=8)),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)
    residual_std = float(np.std(y_test - y_pred))

    joblib.dump({"pipeline": pipeline, "feature_names": FEATURE_NAMES}, model_path)

    metadata = TrainingMetadata(
        model_version=MODEL_VERSION,
        model_path=str(model_path),
        trained_at=datetime.utcnow().isoformat(),
        feature_names=FEATURE_NAMES,
        training_samples=len(X_train),
        mae=float(mae),
        rmse=float(rmse),
        r2=float(r2),
        residual_std=residual_std,
    )

    import json

    with meta_path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(metadata), fh, indent=2)

    # Log to MLflow if available
    try:
        import mlflow

        mlflow.set_experiment("readiness_model")
        with mlflow.start_run(run_name=MODEL_VERSION):
            mlflow.log_params({"model": "RandomForestRegressor", "n_estimators": 200, "max_depth": 8})
            mlflow.log_metrics({"mae": metadata.mae, "rmse": metadata.rmse, "r2": metadata.r2})
            mlflow.log_metric("residual_std", metadata.residual_std)
            mlflow.log_artifact(str(model_path))
            mlflow.log_dict(asdict(metadata), str(meta_path))
    except Exception:
        # MLflow is optional during seeding; ignore errors
        pass

    return asdict(metadata)


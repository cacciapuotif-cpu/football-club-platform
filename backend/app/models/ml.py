"""ML Prediction and Model Tracking models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class OverloadRiskLevel(str, Enum):
    """Overload risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThresholdLevel(str, Enum):
    """Performance threshold levels."""

    ATTENTION = "attenzione"
    NEUTRAL = "neutro"
    GROWING = "in_crescita"


class MLPrediction(SQLModel, table=True):
    """ML prediction results for a player."""

    __tablename__ = "ml_predictions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    prediction_date: datetime

    # Expected Performance
    expected_performance: float  # 0-100
    confidence_lower: float
    confidence_upper: float
    threshold: ThresholdLevel

    # Overload Risk
    overload_risk_level: OverloadRiskLevel
    overload_probability: float  # 0-1
    overload_confidence_lower: float
    overload_confidence_upper: float

    # Model metadata
    model_version: str = Field(max_length=50)
    model_health: str = Field(max_length=20)  # OK, WARN, ALERT

    # Explainability
    feature_importances: dict = Field(default={}, sa_column=Column(JSON))
    local_contributions: dict = Field(default={}, sa_column=Column(JSON))
    natural_language_explanation: str | None = Field(default=None, sa_column=Column(Text))

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class MLModelVersion(SQLModel, table=True):
    """Track ML model versions and metrics."""

    __tablename__ = "ml_model_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    version: str = Field(unique=True, max_length=50)
    trained_at: datetime

    # Training metadata
    training_samples: int
    features_count: int
    features_hash: str = Field(max_length=64)

    # Metrics - Regression (Performance Prediction)
    mae: float | None = None
    rmse: float | None = None
    r2: float | None = None

    # Metrics - Classification (Overload Risk)
    auc: float | None = None
    f1: float | None = None
    precision: float | None = None
    recall: float | None = None
    brier_score: float | None = None

    # Model path
    model_path: str = Field(max_length=500)

    # Status
    is_active: bool = Field(default=False)
    is_production: bool = Field(default=False)

    # Notes
    notes: str | None = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class DriftMetrics(SQLModel, table=True):
    """Track model drift metrics over time."""

    __tablename__ = "drift_metrics"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_version: str = Field(max_length=50)
    check_date: datetime

    # PSI (Population Stability Index) per feature group
    psi_carichi: float  # Training loads
    psi_wellness: float  # Wellness/recovery
    psi_psicologico: float  # Psychological
    psi_kpi_tecnici: float  # Technical KPIs

    # Performance degradation
    mae_current: float
    mae_baseline: float
    mae_degradation_pct: float

    # Status
    status: str = Field(max_length=20)  # OK, WARN, ALERT
    warnings: list[str] = Field(default=[], sa_column=Column(JSON))
    actions_taken: list[str] = Field(default=[], sa_column=Column(JSON))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

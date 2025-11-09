"""Seed step to generate ML predictions using the readiness model."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.inference_service import ensure_model_ready
from app.ml.pipelines.train_readiness import train_readiness_model
from app.models.ml import (
    DriftMetrics,
    MLModelVersion,
    MLPrediction,
    OverloadRiskLevel,
    ThresholdLevel,
)
from app.models.organization import Organization
from app.models.player import Player, PlayerRole
from app.models.player_session import PlayerSession
from app.models.session import TrainingSession


def _position_code(role: PlayerRole | None) -> int:
    mapping: Dict[str, int] = {
        "GK": 0,
        "DF": 1,
        "MF": 2,
        "FW": 3,
    }
    if role is None:
        return 2
    return mapping.get(role.value if isinstance(role, PlayerRole) else str(role), 2)


def _age_years(date_of_birth: datetime | None) -> float:
    if not date_of_birth:
        return 18.0
    today = datetime.utcnow().date()
    years = today.year - date_of_birth.date().year
    return max(15.0, float(years))


def _session_load(session: Session, player_id: UUID, reference: datetime) -> float:
    cutoff = reference - timedelta(days=30)
    stmt = (
        select(func.coalesce(func.avg(PlayerSession.session_load), 0))
        .join(TrainingSession, PlayerSession.session_id == TrainingSession.id)
        .where(
            PlayerSession.player_id == player_id,
            TrainingSession.session_date >= cutoff,
        )
    )
    value = session.execute(stmt).scalar_one()
    return float(value or 400.0)


def _wellness_score(reference_seed: int) -> float:
    from random import Random

    rng = Random(reference_seed)
    return rng.uniform(55, 95)


def seed(session: Session, _: Dict | None = None) -> Dict[str, Dict[str, int]]:
    """Generate predictions for each player using the readiness model."""
    meta = train_readiness_model()
    service = ensure_model_ready()

    model_version = meta["model_version"]
    trained_at = datetime.fromisoformat(meta["trained_at"])

    # Ensure ML model version record exists
    existing_version = session.get(MLModelVersion, {"version": model_version})
    if existing_version is None:
        model_entry = MLModelVersion(
            version=model_version,
            trained_at=trained_at,
            training_samples=meta["training_samples"],
            features_count=len(meta["feature_names"]),
            features_hash="synthetic",
            mae=meta["mae"],
            rmse=meta["rmse"],
            r2=meta["r2"],
            model_path=meta["model_path"],
            is_active=True,
            is_production=True,
            notes="Synthetic baseline model generated during seeding.",
        )
        session.add(model_entry)

    stats = {"ml_predictions": {"create": 0, "update": 0, "skip": 0}}
    now = datetime.utcnow()

    players = session.execute(select(Player)).scalars().all()
    organizations = {org.id: org for org in session.execute(select(Organization)).scalars()}

    for player in players:
        org = organizations.get(player.organization_id)
        if not org:
            stats["ml_predictions"]["skip"] += 1
            continue

        feature_map = {
            "age_years": _age_years(player.date_of_birth),
            "position_code": float(_position_code(player.role_primary)),
            "session_load": _session_load(session, player.id, now),
            "wellness_score": _wellness_score(player.id.int >> 64),
        }

        prediction = service.predict(feature_map)

        # Upsert prediction (one per player per day)
        prediction_date = datetime(now.year, now.month, now.day)
        existing = session.execute(
            select(MLPrediction).where(
                MLPrediction.player_id == player.id,
                MLPrediction.prediction_date == prediction_date,
            )
        ).scalar_one_or_none()

        if existing:
            existing.expected_performance = prediction.expected_performance
            existing.confidence_lower = prediction.confidence_lower
            existing.confidence_upper = prediction.confidence_upper
            existing.threshold = prediction.threshold
            existing.overload_risk_level = prediction.overload_risk_level
            existing.overload_probability = prediction.overload_probability
            existing.overload_confidence_lower = prediction.confidence_lower
            existing.overload_confidence_upper = prediction.confidence_upper
            existing.model_version = prediction.model_version
            existing.model_health = "OK"
            existing.feature_importances = prediction.feature_importances
            existing.local_contributions = prediction.feature_importances
            existing.natural_language_explanation = (
                f"Expected performance {prediction.expected_performance:.1f} ("
                f"{prediction.threshold.value}), overload risk {prediction.overload_risk_level.value}."
            )
            stats["ml_predictions"]["update"] += 1
        else:
            session.add(
                MLPrediction(
                    player_id=player.id,
                    organization_id=player.organization_id,
                    prediction_date=prediction_date,
                    expected_performance=prediction.expected_performance,
                    confidence_lower=prediction.confidence_lower,
                    confidence_upper=prediction.confidence_upper,
                    threshold=prediction.threshold,
                    overload_risk_level=prediction.overload_risk_level,
                    overload_probability=prediction.overload_probability,
                    overload_confidence_lower=prediction.confidence_lower,
                    overload_confidence_upper=prediction.confidence_upper,
                    model_version=prediction.model_version,
                    model_health="OK",
                    feature_importances=prediction.feature_importances,
                    local_contributions=prediction.feature_importances,
                    natural_language_explanation=(
                        f"Expected performance {prediction.expected_performance:.1f} ("
                        f"{prediction.threshold.value}), overload risk {prediction.overload_risk_level.value}."
                    ),
                )
            )
            stats["ml_predictions"]["create"] += 1

    # Drift metrics baseline (optional)
    if stats["ml_predictions"]["create"] > 0:
        session.add(
            DriftMetrics(
                model_version=model_version,
                check_date=now,
                psi_carichi=0.0,
                psi_wellness=0.0,
                psi_psicologico=0.0,
                psi_kpi_tecnici=0.0,
                mae_current=meta["mae"],
                mae_baseline=meta["mae"],
                mae_degradation_pct=0.0,
                status="OK",
                warnings=[],
                actions_taken=[],
            )
        )

    return stats


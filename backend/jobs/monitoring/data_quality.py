"""
Monitoring jobs for data completeness, feature drift, and alert health.

Triggered daily via scheduler/CI to ensure seeds and production pipelines remain healthy.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict

from sqlalchemy import func, select

from app.database import async_session_maker, set_rls_context
from app.models.organization import Organization
from app.models.sessions_wellness import Alert, Feature, Prediction, WellnessReading


async def collect_tenant_metrics(tenant_id: str) -> Dict[str, float]:
    async with async_session_maker() as session:
        await set_rls_context(session, tenant_id=tenant_id, user_role="OWNER", user_id="monitoring-job")

        now = datetime.now(timezone.utc)
        day_start = now - timedelta(days=1)

        wellness_query = await session.execute(
            select(func.count()).select_from(WellnessReading).where(WellnessReading.event_ts >= day_start)
        )
        wellness_count = wellness_query.scalar_one()

        prediction_query = await session.execute(
            select(func.count()).select_from(Prediction).where(Prediction.event_ts >= day_start)
        )
        prediction_count = prediction_query.scalar_one()

        alerts_query = await session.execute(
            select(func.count()).select_from(Alert).where(Alert.opened_at >= day_start)
        )
        alerts_count = alerts_query.scalar_one()

        drift_query = await session.execute(
            select(func.avg(Feature.feature_value)).where(Feature.feature_name == "readiness_score").where(
                Feature.event_ts >= day_start
            )
        )
        readiness_avg = drift_query.scalar_one_or_none() or 0.0

        return {
            "wellness_last_24h": float(wellness_count),
            "predictions_last_24h": float(prediction_count),
            "alerts_last_24h": float(alerts_count),
            "readiness_avg_last_24h": float(readiness_avg),
        }


async def run_monitoring() -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}
    async with async_session_maker() as session:
        organizations = (await session.execute(select(Organization))).scalars().all()
        for org in organizations:
            metrics[str(org.id)] = await collect_tenant_metrics(str(org.id))
    return metrics


def main() -> None:
    metrics = asyncio.run(run_monitoring())
    for tenant_id, tenant_metrics in metrics.items():
        print(f"[monitoring] tenant={tenant_id} metrics={tenant_metrics}")


if __name__ == "__main__":
    main()


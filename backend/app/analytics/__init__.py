"""
Analytics modules for sport science calculations.

Includes:
- Training load: ACWR, Monotony, Strain
- Readiness: Composite index based on z-scores
- Alerts: Risk detection and outlier identification
"""

from app.analytics.training_load import (
    calculate_srpe,
    calculate_acwr_rolling,
    calculate_monotony_weekly,
    calculate_strain_weekly,
)
from app.analytics.readiness import (
    calculate_readiness_index,
    calculate_baseline_28d,
    calculate_z_score,
)
from app.analytics.alerts import (
    Alert,
    detect_acwr_alert,
    detect_readiness_alert,
    detect_outlier_alert,
    generate_alerts,
)

__all__ = [
    # Training load
    "calculate_srpe",
    "calculate_acwr_rolling",
    "calculate_monotony_weekly",
    "calculate_strain_weekly",
    # Readiness
    "calculate_readiness_index",
    "calculate_baseline_28d",
    "calculate_z_score",
    # Alerts
    "Alert",
    "detect_acwr_alert",
    "detect_readiness_alert",
    "detect_outlier_alert",
    "generate_alerts",
]


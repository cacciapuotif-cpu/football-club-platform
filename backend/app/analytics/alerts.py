"""
Alerting and outlier detection for player metrics.

Detects risk conditions based on ACWR, Readiness, and z-score outliers.
"""

import math
from datetime import date, timedelta
from typing import Optional

import numpy as np


class Alert:
    """Represents a single alert."""
    
    def __init__(
        self,
        alert_type: str,
        metric: str,
        alert_date: date,
        value: float,
        threshold: str,
        severity: str = "warning"
    ):
        self.type = alert_type
        self.metric = metric
        self.date = alert_date
        self.value = value
        self.threshold = threshold
        self.severity = severity
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "metric": self.metric,
            "date": self.date.isoformat(),
            "value": self.value,
            "threshold": self.threshold,
            "severity": self.severity
        }


def detect_acwr_alert(acwr: Optional[float], alert_date: date) -> Optional[Alert]:
    """
    Detect ACWR alert: outside [0.8, 1.5] range.
    
    Args:
        acwr: ACWR value
        alert_date: Date of the alert
    
    Returns:
        Alert if condition met, None otherwise
    """
    if acwr is None:
        return None
    
    if acwr < 0.8:
        return Alert(
            alert_type="risk_load",
            metric="acwr",
            alert_date=alert_date,
            value=acwr,
            threshold="< 0.8 (low load, detraining risk)",
            severity="warning"
        )
    elif acwr > 1.5:
        return Alert(
            alert_type="risk_load",
            metric="acwr",
            alert_date=alert_date,
            value=acwr,
            threshold="> 1.5 (high spike, injury risk)",
            severity="error"
        )
    
    return None


def detect_readiness_alert(
    readiness_series: list[tuple[date, Optional[float]]],
    threshold: float = 40.0,
    consecutive_days: int = 3
) -> list[Alert]:
    """
    Detect Readiness alert: < threshold for consecutive_days.
    
    Args:
        readiness_series: List of (date, readiness_value) tuples, sorted by date
        threshold: Readiness threshold (default 40)
        consecutive_days: Number of consecutive days required (default 3)
    
    Returns:
        List of alerts
    """
    alerts = []
    
    if len(readiness_series) < consecutive_days:
        return alerts
    
    consecutive_low = 0
    for d, readiness in readiness_series:
        if readiness is not None and readiness < threshold:
            consecutive_low += 1
            if consecutive_low >= consecutive_days:
                # Create alert on the last day of the streak
                alerts.append(Alert(
                    alert_type="risk_fatigue",
                    metric="readiness",
                    alert_date=d,
                    value=readiness,
                    threshold=f"< {threshold} for {consecutive_days} days",
                    severity="error"
                ))
        else:
            consecutive_low = 0
    
    return alerts


def detect_outlier_alert(
    metric_name: str,
    value: Optional[float],
    mean: Optional[float],
    std: Optional[float],
    alert_date: date,
    z_threshold: float = 2.0
) -> Optional[Alert]:
    """
    Detect outlier alert: |z-score| >= threshold.
    
    Args:
        metric_name: Name of the metric
        value: Current value
        mean: Baseline mean
        std: Baseline std
        alert_date: Date of the alert
        z_threshold: Z-score threshold (default 2.0)
    
    Returns:
        Alert if condition met, None otherwise
    """
    if value is None or mean is None or std is None or std == 0:
        return None
    
    z_score = abs((value - mean) / std)
    
    if z_score >= z_threshold:
        direction = "high" if value > mean else "low"
        return Alert(
            alert_type="risk_outlier",
            metric=metric_name,
            alert_date=alert_date,
            value=value,
            threshold=f"|z-score| >= {z_threshold} ({direction})",
            severity="warning" if z_threshold <= 2.5 else "error"
        )
    
    return None


def generate_alerts(
    acwr_series: list[tuple[date, Optional[float]]],
    readiness_series: list[tuple[date, Optional[float]]],
    wellness_data: list[tuple[date, dict[str, Optional[float]]]],
    baseline_28d: dict[str, dict[str, float]],
    date_from: date,
    date_to: date
) -> list[Alert]:
    """
    Generate all alerts for a player in the given date range.
    
    Args:
        acwr_series: List of (date, acwr_value) tuples
        readiness_series: List of (date, readiness_value) tuples
        wellness_data: List of (date, {metric: value}) tuples
        baseline_28d: Baseline statistics for outlier detection
        date_from: Start date
        date_to: End date
    
    Returns:
        List of alerts
    """
    alerts = []
    
    # ACWR alerts
    acwr_map = {d: acwr for d, acwr in acwr_series if date_from <= d <= date_to}
    for d, acwr in acwr_map.items():
        alert = detect_acwr_alert(acwr, d)
        if alert:
            alerts.append(alert)
    
    # Readiness alerts
    readiness_filtered = [
        (d, r) for d, r in readiness_series
        if date_from <= d <= date_to
    ]
    alerts.extend(detect_readiness_alert(readiness_filtered))
    
    # Outlier alerts for specific metrics
    outlier_metrics = ['resting_hr_bpm', 'hrv_ms', 'soreness', 'mood']
    wellness_map = {d: metrics for d, metrics in wellness_data if date_from <= d <= date_to}
    
    for d, metrics in wellness_map.items():
        for metric in outlier_metrics:
            if metric in metrics and metric in baseline_28d:
                value = metrics[metric]
                baseline = baseline_28d[metric]
                alert = detect_outlier_alert(
                    metric,
                    value,
                    baseline['mean'],
                    baseline['std'],
                    d
                )
                if alert:
                    alerts.append(alert)
    
    # Sort by date
    alerts.sort(key=lambda a: a.date)
    
    return alerts


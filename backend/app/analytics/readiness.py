"""
Readiness Index calculation based on z-scores of wellness metrics.

Composite index (0-100) using rolling 28-day baseline for normalization.
"""

import math
from datetime import date, timedelta
from typing import Optional

import numpy as np


def calculate_z_score(value: Optional[float], mean: Optional[float], std: Optional[float]) -> Optional[float]:
    """
    Calculate z-score: (value - mean) / std
    
    Returns None if insufficient data.
    """
    if value is None or mean is None or std is None or std == 0:
        return None
    return (value - mean) / std


def calculate_readiness_index(
    hrv_ms: Optional[float],
    resting_hr_bpm: Optional[float],
    sleep_quality: Optional[float],
    soreness: Optional[float],
    stress: Optional[float],
    mood: Optional[float],
    body_weight_kg: Optional[float],
    baseline_28d: dict[str, dict[str, float]]  # {metric: {mean, std}}
) -> Optional[float]:
    """
    Calculate Readiness Index (0-100) using z-scores.
    
    Formula:
    - Positive contributions: hrv_ms (+), sleep_quality (+), mood (+)
    - Negative contributions: resting_hr_bpm (-), soreness (-), stress (-), body_weight_kg (-, mild)
    
    Baseline is 50 (neutral). Each z-score contributes proportionally.
    
    Args:
        hrv_ms: Heart rate variability in ms
        resting_hr_bpm: Resting heart rate in bpm
        sleep_quality: Sleep quality score (1-10)
        soreness: Muscle soreness (1-10)
        stress: Stress level (1-10)
        mood: Mood score (1-10)
        body_weight_kg: Body weight in kg
        baseline_28d: Dict with mean and std for each metric over 28 days
    
    Returns:
        Readiness index (0-100), or None if insufficient data
    """
    # Calculate z-scores for each metric
    z_scores = {}
    
    # HRV (positive - higher is better)
    if hrv_ms is not None and 'hrv_ms' in baseline_28d:
        z = calculate_z_score(hrv_ms, baseline_28d['hrv_ms']['mean'], baseline_28d['hrv_ms']['std'])
        if z is not None:
            z_scores['hrv_ms'] = z
    
    # Resting HR (negative - lower is better)
    if resting_hr_bpm is not None and 'resting_hr_bpm' in baseline_28d:
        z = calculate_z_score(resting_hr_bpm, baseline_28d['resting_hr_bpm']['mean'], baseline_28d['resting_hr_bpm']['std'])
        if z is not None:
            z_scores['resting_hr_bpm'] = -z  # Invert (lower HR = better)
    
    # Sleep quality (positive)
    if sleep_quality is not None and 'sleep_quality' in baseline_28d:
        z = calculate_z_score(sleep_quality, baseline_28d['sleep_quality']['mean'], baseline_28d['sleep_quality']['std'])
        if z is not None:
            z_scores['sleep_quality'] = z
    
    # Soreness (negative - lower is better)
    if soreness is not None and 'soreness' in baseline_28d:
        z = calculate_z_score(soreness, baseline_28d['soreness']['mean'], baseline_28d['soreness']['std'])
        if z is not None:
            z_scores['soreness'] = -z  # Invert
    
    # Stress (negative - lower is better)
    if stress is not None and 'stress' in baseline_28d:
        z = calculate_z_score(stress, baseline_28d['stress']['mean'], baseline_28d['stress']['std'])
        if z is not None:
            z_scores['stress'] = -z  # Invert
    
    # Mood (positive)
    if mood is not None and 'mood' in baseline_28d:
        z = calculate_z_score(mood, baseline_28d['mood']['mean'], baseline_28d['mood']['std'])
        if z is not None:
            z_scores['mood'] = z
    
    # Body weight (negative, mild - lower is better but less impact)
    if body_weight_kg is not None and 'body_weight_kg' in baseline_28d:
        z = calculate_z_score(body_weight_kg, baseline_28d['body_weight_kg']['mean'], baseline_28d['body_weight_kg']['std'])
        if z is not None:
            z_scores['body_weight_kg'] = -z * 0.5  # Mild contribution (half weight)
    
    if not z_scores:
        return None
    
    # Weighted average of z-scores (normalized to 0-100 scale)
    # Equal weights for all metrics (can be adjusted)
    weights = {
        'hrv_ms': 0.20,
        'resting_hr_bpm': 0.15,
        'sleep_quality': 0.20,
        'soreness': 0.15,
        'stress': 0.15,
        'mood': 0.10,
        'body_weight_kg': 0.05,  # Mild weight
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for metric, z in z_scores.items():
        weight = weights.get(metric, 0.1)
        weighted_sum += z * weight
        total_weight += weight
    
    if total_weight == 0:
        return None
    
    # Normalize: z-score of 0 = 50 (baseline), scale to 0-100
    # Assuming z-scores typically range from -3 to +3
    # Map: -3 -> 0, 0 -> 50, +3 -> 100
    normalized_z = weighted_sum / total_weight
    readiness = 50 + (normalized_z * 16.67)  # Scale factor: 50 / 3 ≈ 16.67
    
    # Clamp to 0-100
    readiness = max(0.0, min(100.0, readiness))
    
    return readiness


def calculate_baseline_28d(
    wellness_data: list[tuple[date, dict[str, Optional[float]]]],
    target_date: date
) -> dict[str, dict[str, float]]:
    """
    Calculate 28-day baseline (mean and std) for each metric.
    
    Args:
        wellness_data: List of (date, {metric: value}) tuples, sorted by date
        target_date: Date to calculate baseline up to (exclusive)
    
    Returns:
        Dict with {metric: {mean, std}} for each metric
    """
    date_from = target_date - timedelta(days=28)
    
    # Filter data within 28-day window
    baseline_data = [
        (d, metrics) for d, metrics in wellness_data
        if date_from <= d < target_date
    ]
    
    if not baseline_data:
        return {}
    
    # Collect values for each metric
    metric_values = {}
    for _, metrics in baseline_data:
        for metric, value in metrics.items():
            if value is not None:
                if metric not in metric_values:
                    metric_values[metric] = []
                metric_values[metric].append(value)
    
    # Calculate mean and std for each metric
    baseline = {}
    for metric, values in metric_values.items():
        if len(values) >= 3:  # Need at least 3 data points
            baseline[metric] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            }
    
    return baseline


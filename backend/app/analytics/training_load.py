"""
Training load analytics: ACWR, Monotony, Strain calculations.

Sport science calculations for monitoring training load and injury risk.
"""

import math
from datetime import date, timedelta
from typing import Optional

import numpy as np


def calculate_srpe(duration_minutes: float, rpe_post: float) -> float:
    """
    Calculate session RPE (sRPE).
    
    sRPE = duration_minutes * rpe_post
    
    Args:
        duration_minutes: Session duration in minutes
        rpe_post: Post-session RPE (1-10)
    
    Returns:
        sRPE value
    """
    return duration_minutes * rpe_post


def calculate_acwr_rolling(
    daily_srpe: list[tuple[date, float]],
    window_short: int = 7,
    window_long: int = 28
) -> list[tuple[date, Optional[float]]]:
    """
    Calculate ACWR (Acute:Chronic Workload Ratio) with rolling windows.
    
    ACWR = mean(short_window) / mean(long_window)
    
    Args:
        daily_srpe: List of (date, srpe_value) tuples, sorted by date
        window_short: Short window in days (default 7)
        window_long: Long window in days (default 28)
    
    Returns:
        List of (date, acwr_value) tuples. acwr_value is None if insufficient data.
    """
    if not daily_srpe or len(daily_srpe) < window_long:
        return []
    
    acwr_series = []
    
    for i in range(window_long - 1, len(daily_srpe)):
        current_date, _ = daily_srpe[i]
        
        # Get short window (last window_short days including current)
        short_window_data = daily_srpe[max(0, i - window_short + 1):i + 1]
        short_values = [srpe for _, srpe in short_window_data]
        
        # Get long window (last window_long days including current)
        long_window_data = daily_srpe[max(0, i - window_long + 1):i + 1]
        long_values = [srpe for _, srpe in long_window_data]
        
        if len(short_values) < window_short - 2 or len(long_values) < window_long - 5:
            acwr_series.append((current_date, None))
            continue
        
        acute = np.mean(short_values)
        chronic = np.mean(long_values)
        
        if chronic > 0:
            acwr = acute / chronic
            acwr_series.append((current_date, float(acwr)))
        else:
            acwr_series.append((current_date, None))
    
    return acwr_series


def calculate_monotony_weekly(
    daily_srpe: list[tuple[date, float]]
) -> list[tuple[date, Optional[float]]]:
    """
    Calculate Monotony = weekly_mean / weekly_std for each week.
    
    Monotony measures training load variability. Higher values indicate more monotonous training.
    Handles sigma ≈ 0 by using minimum std of 0.1.
    
    Args:
        daily_srpe: List of (date, srpe_value) tuples, sorted by date
    
    Returns:
        List of (week_start_date, monotony_value) tuples. None if insufficient data.
    """
    if not daily_srpe:
        return []
    
    # Group by week (Monday as week start)
    weekly_data = {}
    for d, srpe in daily_srpe:
        # Get Monday of the week
        days_since_monday = d.weekday()
        week_start = d - timedelta(days=days_since_monday)
        
        if week_start not in weekly_data:
            weekly_data[week_start] = []
        weekly_data[week_start].append(srpe)
    
    monotony_series = []
    for week_start in sorted(weekly_data.keys()):
        week_values = weekly_data[week_start]
        
        if len(week_values) < 3:  # Need at least 3 days for meaningful std
            monotony_series.append((week_start, None))
            continue
        
        mean = np.mean(week_values)
        std = np.std(week_values, ddof=1)  # Sample std
        
        # Handle sigma ≈ 0
        std = max(std, 0.1)
        
        monotony = mean / std
        monotony_series.append((week_start, float(monotony)))
    
    return monotony_series


def calculate_strain_weekly(
    daily_srpe: list[tuple[date, float]],
    monotony_weekly: list[tuple[date, Optional[float]]]
) -> list[tuple[date, Optional[float]]]:
    """
    Calculate Strain = weekly_total_load * Monotony for each week.
    
    Strain combines total load with monotony to assess training stress.
    
    Args:
        daily_srpe: List of (date, srpe_value) tuples, sorted by date
        monotony_weekly: List of (week_start_date, monotony_value) from calculate_monotony_weekly
    
    Returns:
        List of (week_start_date, strain_value) tuples. None if monotony is None.
    """
    if not daily_srpe:
        return []
    
    # Group by week and sum
    weekly_totals = {}
    for d, srpe in daily_srpe:
        days_since_monday = d.weekday()
        week_start = d - timedelta(days=days_since_monday)
        
        if week_start not in weekly_totals:
            weekly_totals[week_start] = 0.0
        weekly_totals[week_start] += srpe
    
    # Create monotony lookup
    monotony_map = {week_start: monotony for week_start, monotony in monotony_weekly}
    
    strain_series = []
    for week_start in sorted(weekly_totals.keys()):
        weekly_load = weekly_totals[week_start]
        monotony = monotony_map.get(week_start)
        
        if monotony is not None:
            strain = weekly_load * monotony
            strain_series.append((week_start, float(strain)))
        else:
            strain_series.append((week_start, None))
    
    return strain_series


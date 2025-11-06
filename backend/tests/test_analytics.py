"""
Unit tests for analytics modules: ACWR, Monotony, Strain, Readiness.
"""

import pytest
from datetime import date, timedelta

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


class TestTrainingLoad:
    """Tests for training load calculations."""
    
    def test_calculate_srpe(self):
        """Test sRPE calculation."""
        assert calculate_srpe(75.0, 6.0) == 450.0
        assert calculate_srpe(90.0, 8.0) == 720.0
        assert calculate_srpe(60.0, 5.0) == 300.0
    
    def test_calculate_acwr_rolling(self):
        """Test ACWR rolling calculation."""
        # Create 35 days of data
        base_date = date.today() - timedelta(days=35)
        daily_srpe = [
            (base_date + timedelta(days=i), 300.0 + (i % 7) * 50)
            for i in range(35)
        ]
        
        acwr_series = calculate_acwr_rolling(daily_srpe, window_short=7, window_long=28)
        
        # Should have results starting from day 28
        assert len(acwr_series) > 0
        assert all(d >= base_date + timedelta(days=27) for d, _ in acwr_series)
        assert all(acwr is None or 0 < acwr < 5 for _, acwr in acwr_series)
    
    def test_calculate_monotony_weekly(self):
        """Test Monotony weekly calculation."""
        base_date = date.today() - timedelta(days=21)
        daily_srpe = [
            (base_date + timedelta(days=i), 300.0 if i % 2 == 0 else 350.0)
            for i in range(21)
        ]
        
        monotony = calculate_monotony_weekly(daily_srpe)
        
        assert len(monotony) > 0
        assert all(m is None or m > 0 for _, m in monotony)
    
    def test_calculate_strain_weekly(self):
        """Test Strain weekly calculation."""
        base_date = date.today() - timedelta(days=14)
        daily_srpe = [
            (base_date + timedelta(days=i), 300.0)
            for i in range(14)
        ]
        
        monotony_weekly = calculate_monotony_weekly(daily_srpe)
        strain_weekly = calculate_strain_weekly(daily_srpe, monotony_weekly)
        
        assert len(strain_weekly) > 0
        assert all(s is None or s >= 0 for _, s in strain_weekly)


class TestReadiness:
    """Tests for readiness index calculations."""
    
    def test_calculate_z_score(self):
        """Test z-score calculation."""
        assert calculate_z_score(100.0, 100.0, 10.0) == 0.0
        assert abs(calculate_z_score(110.0, 100.0, 10.0) - 1.0) < 0.001
        assert calculate_z_score(None, 100.0, 10.0) is None
        assert calculate_z_score(100.0, None, 10.0) is None
        assert calculate_z_score(100.0, 100.0, 0.0) is None
    
    def test_calculate_readiness_index(self):
        """Test readiness index calculation."""
        baseline = {
            'hrv_ms': {'mean': 50.0, 'std': 10.0},
            'resting_hr_bpm': {'mean': 60.0, 'std': 5.0},
            'sleep_quality': {'mean': 7.0, 'std': 1.0},
            'soreness': {'mean': 3.0, 'std': 1.0},
            'stress': {'mean': 4.0, 'std': 1.0},
            'mood': {'mean': 7.0, 'std': 1.0},
            'body_weight_kg': {'mean': 70.0, 'std': 2.0},
        }
        
        # Test with baseline values (should be around 50)
        readiness = calculate_readiness_index(
            hrv_ms=50.0,
            resting_hr_bpm=60.0,
            sleep_quality=7.0,
            soreness=3.0,
            stress=4.0,
            mood=7.0,
            body_weight_kg=70.0,
            baseline_28d=baseline
        )
        
        assert readiness is not None
        assert 0 <= readiness <= 100
        # Should be close to 50 (baseline)
        assert 40 <= readiness <= 60
    
    def test_calculate_baseline_28d(self):
        """Test baseline calculation."""
        base_date = date.today() - timedelta(days=30)
        wellness_data = [
            (base_date + timedelta(days=i), {
                'hrv_ms': 50.0 + (i % 5),
                'resting_hr_bpm': 60.0 + (i % 3),
                'sleep_quality': 7.0,
            })
            for i in range(30)
        ]
        
        target_date = date.today()
        baseline = calculate_baseline_28d(wellness_data, target_date)
        
        assert 'hrv_ms' in baseline
        assert 'resting_hr_bpm' in baseline
        assert 'sleep_quality' in baseline
        assert baseline['hrv_ms']['mean'] > 0
        assert baseline['hrv_ms']['std'] >= 0


"""Tests for calculation service."""
import pytest
from decimal import Decimal

from app.services.calculations import (
    calculate_bmi,
    calculate_pass_accuracy,
    calculate_shot_accuracy,
    calculate_dribble_success,
    calculate_performance_index
)


def test_calculate_bmi():
    """Test BMI calculation."""
    # Normal case
    bmi = calculate_bmi(Decimal("176.0"), Decimal("66.5"))
    assert bmi is not None
    assert 21.0 <= bmi <= 22.0

    # Edge cases
    assert calculate_bmi(None, Decimal("70")) is None
    assert calculate_bmi(Decimal("180"), None) is None
    assert calculate_bmi(Decimal("0"), Decimal("70")) is None


def test_calculate_pass_accuracy():
    """Test pass accuracy calculation."""
    # 100% accuracy
    assert calculate_pass_accuracy(10, 10) == Decimal("100.00")

    # 50% accuracy
    assert calculate_pass_accuracy(5, 10) == Decimal("50.00")

    # Zero attempts
    assert calculate_pass_accuracy(5, 0) is None

    # Edge case: more completed than attempted (should be caught by validation)
    accuracy = calculate_pass_accuracy(15, 10)
    assert accuracy == Decimal("150.00")  # Should be prevented by schema validation


def test_calculate_shot_accuracy():
    """Test shot accuracy calculation."""
    assert calculate_shot_accuracy(3, 5) == Decimal("60.00")
    assert calculate_shot_accuracy(0, 5) == Decimal("0.00")
    assert calculate_shot_accuracy(2, 0) is None


def test_calculate_dribble_success():
    """Test dribble success rate calculation."""
    # 5 successful, 2 failed = 71.43%
    success = calculate_dribble_success(5, 2)
    assert success is not None
    assert 71.0 <= success <= 72.0

    # All successful
    assert calculate_dribble_success(10, 0) == Decimal("100.00")

    # None attempted
    assert calculate_dribble_success(0, 0) is None


def test_calculate_performance_index():
    """Test performance index calculation."""
    # Test with realistic midfielder data
    index = calculate_performance_index(
        pass_accuracy_pct=Decimal("88.0"),
        progressive_passes=12,
        interceptions=6,
        successful_dribbles=5,
        sprints_over_25kmh=18,
        resting_hr_bpm=58,
        yoyo_level=Decimal("22.0"),
        distance_km=Decimal("10.5"),
        sleep_hours=Decimal("8.0"),
        coach_rating=Decimal("7.5"),
        rpe=Decimal("7.0")
    )

    # Should be between 0 and 100
    assert 0 <= index <= 100

    # With good stats, should be in upper range
    assert index >= 50


def test_performance_index_with_nulls():
    """Test performance index calculation with missing data."""
    index = calculate_performance_index(
        pass_accuracy_pct=None,  # Missing
        progressive_passes=10,
        interceptions=5,
        successful_dribbles=4,
        sprints_over_25kmh=15,
        resting_hr_bpm=60,
        yoyo_level=None,  # Missing
        distance_km=Decimal("9.0"),
        sleep_hours=None,  # Missing
        coach_rating=None,  # Missing
        rpe=Decimal("6.5")
    )

    # Should still calculate
    assert 0 <= index <= 100


def test_performance_index_poor_stats():
    """Test performance index with poor performance."""
    index = calculate_performance_index(
        pass_accuracy_pct=Decimal("50.0"),  # Low
        progressive_passes=2,  # Low
        interceptions=1,  # Low
        successful_dribbles=0,  # Low
        sprints_over_25kmh=5,  # Low
        resting_hr_bpm=75,  # High (worse)
        yoyo_level=Decimal("15.0"),  # Low
        distance_km=Decimal("6.0"),  # Low
        sleep_hours=Decimal("5.0"),  # Low
        coach_rating=Decimal("5.0"),  # Low
        rpe=Decimal("9.0")  # High (tired)
    )

    # Should be in lower range
    assert index < 50


def test_performance_index_excellent_stats():
    """Test performance index with excellent performance."""
    index = calculate_performance_index(
        pass_accuracy_pct=Decimal("95.0"),
        progressive_passes=20,
        interceptions=10,
        successful_dribbles=8,
        sprints_over_25kmh=25,
        resting_hr_bpm=48,  # Very low (excellent)
        yoyo_level=Decimal("28.0"),
        distance_km=Decimal("13.0"),
        sleep_hours=Decimal("9.0"),
        coach_rating=Decimal("9.5"),
        rpe=Decimal("7.0")  # Optimal
    )

    # Should be in upper range
    assert index >= 70

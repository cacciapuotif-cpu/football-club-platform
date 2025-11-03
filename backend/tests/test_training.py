"""Test training/RPE endpoints."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest


def test_upsert_rpe_create_success(client, test_player, test_session):
    """Test creating RPE for a player session."""
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session.id),
        "rpe": 7.5
    }

    response = client.post("/api/v1/training/rpe", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == str(test_player.id)
    assert data["session_id"] == str(test_session.id)
    assert float(data["rpe"]) == 7.5
    assert data["duration_min"] == test_session.duration_min
    # session_load = 7.5 * duration_min
    expected_load = 7.5 * test_session.duration_min
    assert float(data["session_load"]) == expected_load
    assert "updated_at" in data


def test_upsert_rpe_update_existing(client, test_player, test_session):
    """Test updating RPE for an existing player session."""
    # Create first
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session.id),
        "rpe": 6.0
    }
    response1 = client.post("/api/v1/training/rpe", json=payload)
    assert response1.status_code == 200

    # Update with new RPE
    payload["rpe"] = 8.5
    response2 = client.post("/api/v1/training/rpe", json=payload)

    assert response2.status_code == 200
    data = response2.json()
    assert float(data["rpe"]) == 8.5
    expected_load = 8.5 * test_session.duration_min
    assert float(data["session_load"]) == expected_load


def test_upsert_rpe_invalid_rpe_too_high(client, test_player, test_session):
    """Test RPE validation - value too high."""
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session.id),
        "rpe": 11.0  # Invalid: > 10
    }

    response = client.post("/api/v1/training/rpe", json=payload)
    assert response.status_code == 422  # Validation error


def test_upsert_rpe_invalid_rpe_negative(client, test_player, test_session):
    """Test RPE validation - negative value."""
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session.id),
        "rpe": -1.0  # Invalid: < 0
    }

    response = client.post("/api/v1/training/rpe", json=payload)
    assert response.status_code == 422  # Validation error


def test_upsert_rpe_session_not_found(client, test_player):
    """Test RPE with non-existent session."""
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(uuid4()),  # Random UUID
        "rpe": 7.0
    }

    response = client.post("/api/v1/training/rpe", json=payload)
    assert response.status_code == 404


def test_upsert_rpe_session_no_duration(client, test_player, test_session_no_duration):
    """Test RPE with session that has no duration."""
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session_no_duration.id),
        "rpe": 7.0
    }

    response = client.post("/api/v1/training/rpe", json=payload)
    assert response.status_code == 422  # Unprocessable entity


def test_weekly_load_empty(client, test_player):
    """Test weekly load with no RPE data."""
    response = client.get(f"/api/v1/training/players/{test_player.id}/weekly-load?weeks=8")

    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == str(test_player.id)
    assert len(data["weeks"]) == 8
    assert float(data["total_current_week"]) == 0.0

    # All weeks should be 0
    for week in data["weeks"]:
        assert float(week["weekly_load"]) == 0.0


def test_weekly_load_with_data(client, test_player, test_session):
    """Test weekly load with actual RPE data."""
    # Add RPE
    payload = {
        "player_id": str(test_player.id),
        "session_id": str(test_session.id),
        "rpe": 7.0
    }
    client.post("/api/v1/training/rpe", json=payload)

    # Get weekly load
    response = client.get(f"/api/v1/training/players/{test_player.id}/weekly-load?weeks=8")

    assert response.status_code == 200
    data = response.json()
    assert len(data["weeks"]) == 8

    # Current week should have non-zero load
    assert float(data["total_current_week"]) > 0


def test_weekly_load_custom_weeks(client, test_player):
    """Test weekly load with custom number of weeks."""
    response = client.get(f"/api/v1/training/players/{test_player.id}/weekly-load?weeks=4")

    assert response.status_code == 200
    data = response.json()
    assert len(data["weeks"]) == 4


def test_weekly_load_max_weeks(client, test_player):
    """Test weekly load respects max weeks limit."""
    response = client.get(f"/api/v1/training/players/{test_player.id}/weekly-load?weeks=16")

    assert response.status_code == 200
    data = response.json()
    assert len(data["weeks"]) == 16


def test_weekly_load_weeks_too_high(client, test_player):
    """Test weekly load validation - weeks > 16."""
    response = client.get(f"/api/v1/training/players/{test_player.id}/weekly-load?weeks=20")

    assert response.status_code == 422  # Validation error

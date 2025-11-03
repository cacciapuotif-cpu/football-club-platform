"""Tests for API endpoints."""
import pytest
from datetime import date


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_player(client):
    """Test player creation."""
    player_data = {
        "code": "TEST-002",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "2008-05-15",
        "category": "U17",
        "primary_role": "MF",
        "dominant_foot": "RIGHT",
        "shirt_number": 7,
        "years_active": 1
    }

    response = client.post("/api/players", json=player_data)
    assert response.status_code == 201

    data = response.json()
    assert data["code"] == "TEST-002"
    assert data["first_name"] == "John"
    assert "id" in data


def test_create_duplicate_player(client, sample_player):
    """Test that duplicate player codes are rejected."""
    player_data = {
        "code": "TEST-001",  # Same as sample_player
        "first_name": "Duplicate",
        "last_name": "Player",
        "date_of_birth": "2008-05-15",
        "category": "U17",
        "primary_role": "MF",
        "dominant_foot": "RIGHT"
    }

    response = client.post("/api/players", json=player_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_players(client, sample_player):
    """Test getting list of players."""
    response = client.get("/api/players")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
    assert data[0]["code"] == "TEST-001"


def test_get_player_by_id(client, sample_player):
    """Test getting a single player by ID."""
    response = client.get(f"/api/players/{sample_player.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(sample_player.id)
    assert data["code"] == "TEST-001"


def test_get_nonexistent_player(client):
    """Test getting a player that doesn't exist."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/players/{fake_uuid}")
    assert response.status_code == 404


def test_create_session(client, sample_player, sample_session_data):
    """Test creating a session with all metrics."""
    response = client.post("/api/sessions", json=sample_session_data)
    assert response.status_code == 201

    data = response.json()
    assert data["player_id"] == str(sample_player.id)

    # Check calculated metrics
    assert data["metrics_physical"]["bmi"] is not None
    assert data["metrics_technical"]["pass_accuracy_pct"] is not None

    # Check analytics outputs
    assert data["analytics_outputs"] is not None
    assert "performance_index" in data["analytics_outputs"]
    assert 0 <= float(data["analytics_outputs"]["performance_index"]) <= 100


def test_create_session_invalid_player(client, sample_session_data):
    """Test creating a session with invalid player code."""
    sample_session_data["player_code"] = "INVALID-CODE"

    response = client.post("/api/sessions", json=sample_session_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_sessions(client, sample_player, sample_session_data):
    """Test getting sessions."""
    # Create a session first
    client.post("/api/sessions", json=sample_session_data)

    # Get sessions
    response = client.get(f"/api/sessions?player_id={sample_player.id}")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
    assert data[0]["player_id"] == str(sample_player.id)


def test_delete_player_cascades(client, sample_player, sample_session_data):
    """Test that deleting a player cascades to sessions."""
    # Create a session
    session_response = client.post("/api/sessions", json=sample_session_data)
    assert session_response.status_code == 201

    # Delete player
    delete_response = client.delete(f"/api/players/{sample_player.id}")
    assert delete_response.status_code == 204

    # Try to get sessions (should be empty)
    sessions_response = client.get(f"/api/sessions?player_id={sample_player.id}")
    assert sessions_response.status_code == 200
    assert len(sessions_response.json()) == 0


def test_analytics_trend(client, sample_player, sample_session_data):
    """Test analytics trend endpoint."""
    # Create some sessions
    for i in range(3):
        session_data = sample_session_data.copy()
        session_data["session"]["session_date"] = f"2025-10-{10+i:02d}"
        client.post("/api/sessions", json=session_data)

    # Get trend
    response = client.get(f"/api/analytics/player/{sample_player.id}/trend")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    assert "performance_index" in data[0]


def test_analytics_summary(client, sample_player, sample_session_data):
    """Test analytics summary endpoint."""
    # Create session
    client.post("/api/sessions", json=sample_session_data)

    # Get summary
    response = client.get(f"/api/analytics/player/{sample_player.id}/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["player_id"] == str(sample_player.id)
    assert "avg_performance_index" in data
    assert "training_stats" in data
    assert "match_stats" in data


def test_export_csv(client, sample_player, sample_session_data):
    """Test CSV export."""
    # Create session
    client.post("/api/sessions", json=sample_session_data)

    # Export CSV
    response = client.get(f"/api/export/sessions.csv?player_id={sample_player.id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # Check CSV content
    content = response.text
    assert "player_code" in content
    assert "TEST-001" in content


def test_export_json(client, sample_player, sample_session_data):
    """Test JSON export."""
    # Create session
    client.post("/api/sessions", json=sample_session_data)

    # Export JSON
    response = client.get(f"/api/export/sessions.json?player_id={sample_player.id}")
    assert response.status_code == 200

    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) >= 1


def test_validation_pass_accuracy(client, sample_player, sample_session_data):
    """Test that validation catches impossible pass accuracy."""
    # More completed than attempted
    sample_session_data["metrics_technical"]["passes_completed"] = 100
    sample_session_data["metrics_technical"]["passes_attempted"] = 50

    response = client.post("/api/sessions", json=sample_session_data)
    assert response.status_code == 422  # Validation error


def test_validation_shot_accuracy(client, sample_player, sample_session_data):
    """Test that validation catches impossible shot accuracy."""
    # More on target than total shots
    sample_session_data["metrics_technical"]["shots_on_target"] = 10
    sample_session_data["metrics_technical"]["shots"] = 5

    response = client.post("/api/sessions", json=sample_session_data)
    assert response.status_code == 422  # Validation error

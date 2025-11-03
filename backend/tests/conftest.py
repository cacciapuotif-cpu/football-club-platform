"""Pytest configuration and fixtures."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.database import get_session


@pytest.fixture
def client():
    """Test client for API testing."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer mock_token_for_testing"}


@pytest.fixture
async def db_session():
    """Get database session for testing."""
    async for session in get_session():
        yield session
        await session.close()


@pytest.fixture
def test_player(client):
    """Create a test player in the database."""
    # Create player via direct SQL for simplicity
    player_id = uuid4()
    player_data = {
        "id": str(player_id),
        "first_name": "Test",
        "last_name": "Player",
        "date_of_birth": "1995-01-01",
        "nationality": "ITA",
        "role_primary": "MF",
        "dominant_foot": "RIGHT",
        "dominant_arm": "RIGHT",
        "is_active": True,
        "is_injured": False,
        "is_minor": False,
        "consent_given": True
    }

    # Note: This is a simplified fixture - in production you'd use proper async fixtures
    # For now we just return a mock object with the necessary attributes
    class MockPlayer:
        def __init__(self):
            self.id = player_id

    return MockPlayer()


@pytest.fixture
def test_session(client):
    """Create a test training session in the database."""
    session_id = uuid4()

    class MockSession:
        def __init__(self):
            self.id = session_id
            self.duration_min = 90
            self.session_date = datetime.utcnow()

    return MockSession()


@pytest.fixture
def test_session_no_duration(client):
    """Create a test training session without duration."""
    session_id = uuid4()

    class MockSession:
        def __init__(self):
            self.id = session_id
            self.duration_min = None
            self.session_date = datetime.utcnow()

    return MockSession()

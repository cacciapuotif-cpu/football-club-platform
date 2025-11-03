"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal

from app.db.database import Base, get_db
from app.main import app
from app.models.models import Player, Session as SessionModel
from app.models.enums import PlayerRole, DominantFoot, SessionType, PlayerStatus

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_player(db_session):
    """Create a sample player for testing."""
    player = Player(
        code="TEST-001",
        first_name="Test",
        last_name="Player",
        date_of_birth=date(2008, 1, 1),
        category="U17",
        primary_role=PlayerRole.MF,
        dominant_foot=DominantFoot.RIGHT,
        shirt_number=10,
        years_active=2
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def sample_session_data():
    """Sample session data payload."""
    return {
        "player_code": "TEST-001",
        "session": {
            "session_date": "2025-10-10",
            "session_type": "TRAINING",
            "minutes_played": 75,
            "coach_rating": 7.5,
            "notes": "Test session",
            "status": "OK"
        },
        "metrics_physical": {
            "height_cm": 176.0,
            "weight_kg": 66.5,
            "resting_hr_bpm": 60,
            "distance_km": 10.5,
            "sprints_over_25kmh": 18,
            "yoyo_level": 22.0,
            "rpe": 7.0,
            "sleep_hours": 8.0
        },
        "metrics_technical": {
            "passes_attempted": 65,
            "passes_completed": 58,
            "progressive_passes": 12,
            "shots": 2,
            "shots_on_target": 1,
            "successful_dribbles": 4,
            "failed_dribbles": 2,
            "ball_losses": 8,
            "ball_recoveries": 10
        },
        "metrics_tactical": {
            "xg": 0.35,
            "xa": 0.22,
            "pressures": 20,
            "interceptions": 6,
            "involvement_pct": 55.0
        },
        "metrics_psych": {
            "attention_score": 75,
            "motivation": 8,
            "stress_management": 7,
            "self_esteem": 8,
            "team_leadership": 6,
            "mood_pre": 7,
            "mood_post": 8
        }
    }

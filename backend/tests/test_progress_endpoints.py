"""
Test endpoints for player progress tracking.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Organization, Player, Team, Season
from app.models.wellness_eav import WellnessSession, WellnessMetric
from app.models.training_eav import TrainingAttendance, TrainingMetric
from app.models.session import TrainingSession
from app.database import async_session_maker


@pytest.fixture
async def test_data():
    """Create test organization, team, and player."""
    async with async_session_maker() as session:
        # Create org
        org = Organization(
            id=uuid4(),
            name="Test FC",
            slug="test-fc",
            country="IT",
            is_active=True,
            benchmark_opt_in=False,
            timezone="Europe/Rome",
            locale="it-IT",
            quota_players=100,
            quota_storage_gb=50,
            current_storage_gb=0.0,
        )
        session.add(org)
        await session.flush()
        
        # Create season
        season = Season(
            id=uuid4(),
            name="2024/25",
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30),
            is_active=True,
            organization_id=org.id,
        )
        session.add(season)
        await session.flush()
        
        # Create team
        team = Team(
            id=uuid4(),
            name="Test Team",
            category="Youth",
            season_id=season.id,
            organization_id=org.id,
        )
        session.add(team)
        await session.flush()
        
        # Create player
        player = Player(
            id=uuid4(),
            first_name="Test",
            last_name="Player",
            date_of_birth=date(2008, 1, 1),
            nationality="IT",
            role_primary="MF",
            organization_id=org.id,
            team_id=team.id,
        )
        session.add(player)
        await session.flush()
        
        await session.commit()
        
        yield org, team, player
        
        # Cleanup
        await session.delete(player)
        await session.delete(team)
        await session.delete(season)
        await session.delete(org)
        await session.commit()


@pytest.fixture
async def wellness_data(test_data):
    """Create 14 days of wellness data."""
    org, team, player = test_data
    async with async_session_maker() as session:
        today = date.today()
        sessions = []
        
        for i in range(14):
            session_date = today - timedelta(days=13 - i)
            
            ws = WellnessSession(
                id=uuid4(),
                player_id=player.id,
                date=session_date,
                source="test",
                organization_id=org.id,
            )
            session.add(ws)
            await session.flush()
            sessions.append(ws)
            
            # Add metrics
            metrics = [
                ("sleep_quality", 7.0 + (i % 3) * 0.5),
                ("fatigue", 3.0 + (i % 4) * 0.3),
                ("soreness", 2.0 + (i % 3) * 0.2),
                ("stress", 4.0 + (i % 2) * 0.5),
                ("mood", 7.0 + (i % 3) * 0.4),
            ]
            
            for metric_key, value in metrics:
                wm = WellnessMetric(
                    id=uuid4(),
                    wellness_session_id=ws.id,
                    metric_key=metric_key,
                    metric_value=value,
                    unit="score",
                )
                session.add(wm)
        
        await session.commit()
        return sessions


@pytest.fixture
async def training_data(test_data):
    """Create 4 training sessions with attendance."""
    org, team, player = test_data
    async with async_session_maker() as session:
        today = date.today()
        sessions = []
        
        for i in range(4):
            session_date = datetime.combine(
                today - timedelta(days=7 - i * 2),
                datetime.min.time()
            )
            
            ts = TrainingSession(
                id=uuid4(),
                session_date=session_date,
                session_type="TRAINING",
                duration_min=90,
                team_id=team.id,
                organization_id=org.id,
            )
            session.add(ts)
            await session.flush()
            sessions.append(ts)
            
            # Add attendance
            att = TrainingAttendance(
                id=uuid4(),
                training_session_id=ts.id,
                player_id=player.id,
                status="present",
                minutes=75,
                rpe_post=5 + (i % 2),
                organization_id=org.id,
            )
            session.add(att)
            await session.flush()
            
            # Add metrics
            tm = TrainingMetric(
                id=uuid4(),
                training_attendance_id=att.id,
                metric_key="total_distance",
                metric_value=5.5 + i * 0.3,
                unit="km",
            )
            session.add(tm)
        
        await session.commit()
        return sessions


@pytest.mark.asyncio
async def test_progress_endpoint(test_data, wellness_data, training_data):
    """Test GET /api/v1/players/{id}/progress."""
    org, team, player = test_data
    
    client = TestClient(app)
    
    response = client.get(
        f"/api/v1/players/{player.id}/progress",
        params={
            "bucket": "weekly",
            "date_from": (date.today() - timedelta(days=14)).isoformat(),
            "date_to": date.today().isoformat(),
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "bucket" in data
    assert "date_from" in data
    assert "date_to" in data
    assert "series" in data
    assert len(data["series"]) > 0
    
    # Check first bucket has expected fields
    first_bucket = data["series"][0]
    assert "bucket_start" in first_bucket
    assert "sleep_quality" in first_bucket or first_bucket.get("sleep_quality") is None
    assert "srpe" in first_bucket or first_bucket.get("srpe") is None


@pytest.mark.asyncio
async def test_training_load_endpoint(test_data, training_data):
    """Test GET /api/v1/players/{id}/training-load."""
    org, team, player = test_data
    
    client = TestClient(app)
    
    response = client.get(
        f"/api/v1/players/{player.id}/training-load",
        params={
            "acute_days": 7,
            "chronic_days": 28,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "series" in data
    assert "acute_days" in data
    assert "chronic_days" in data
    assert "flags" in data
    
    assert data["acute_days"] == 7
    assert data["chronic_days"] == 28
    
    if len(data["series"]) > 0:
        point = data["series"][0]
        assert "date" in point
        assert "srpe" in point


@pytest.mark.asyncio
async def test_overview_endpoint(test_data, wellness_data, training_data):
    """Test GET /api/v1/players/{id}/overview."""
    org, team, player = test_data
    
    client = TestClient(app)
    
    response = client.get(
        f"/api/v1/players/{player.id}/overview",
        params={"period": "28d"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "window_days" in data
    assert "wellness_days_with_data" in data
    assert "wellness_completeness_pct" in data
    assert "last_values" in data
    assert "training_sessions" in data
    assert "present_count" in data
    
    assert data["window_days"] == 28
    assert data["wellness_days_with_data"] >= 0
    assert isinstance(data["wellness_completeness_pct"], (int, float))
    assert isinstance(data["last_values"], dict)


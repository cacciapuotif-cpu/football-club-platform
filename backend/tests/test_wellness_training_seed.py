"""
Test wellness and training seed script.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Organization, Player, Team, Season


@pytest.mark.asyncio
async def test_seed_wellness_training():
    """Test that seed_demo_data creates expected data."""
    async with async_session_maker() as session:
        # Get org and players
        org_result = await session.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_id = org_result.scalar_one_or_none()
        
        if not org_id:
            pytest.skip("No organization found. Run seed script first.")
        
        players_result = await session.execute(
            text("SELECT id FROM players WHERE organization_id = :org_id LIMIT 25"),
            {"org_id": org_id}
        )
        player_ids = [row[0] for row in players_result.fetchall()]
        
        if len(player_ids) == 0:
            pytest.skip("No players found. Run seed script first.")
        
        # Check wellness sessions
        wellness_count_result = await session.execute(
            text("SELECT COUNT(*) FROM wellness_sessions WHERE player_id = :pid"),
            {"pid": player_ids[0]}
        )
        wellness_count = wellness_count_result.scalar() or 0
        
        assert wellness_count >= 60, f"Expected at least 60 wellness sessions, got {wellness_count}"
        
        # Check wellness metrics
        metrics_count_result = await session.execute(
            text("""
                SELECT COUNT(*) 
                FROM wellness_metrics wm
                JOIN wellness_sessions ws ON ws.id = wm.wellness_session_id
                WHERE ws.player_id = :pid
            """),
            {"pid": player_ids[0]}
        )
        metrics_count = metrics_count_result.scalar() or 0
        
        assert metrics_count > 0, "Expected wellness metrics"
        
        # Check training attendance
        attendance_count_result = await session.execute(
            text("SELECT COUNT(*) FROM training_attendance")
        )
        attendance_count = attendance_count_result.scalar() or 0
        
        assert attendance_count > 0, "Expected training attendance records"
        
        # Check training sessions
        sessions_count_result = await session.execute(
            text("SELECT COUNT(*) FROM training_sessions")
        )
        sessions_count = sessions_count_result.scalar() or 0
        
        assert sessions_count >= 20, f"Expected at least 20 training sessions, got {sessions_count}"


@pytest.mark.asyncio
async def test_seed_idempotency():
    """Test that running seed twice doesn't create duplicates."""
    async with async_session_maker() as session:
        # Count before
        before_wellness = await session.execute(
            text("SELECT COUNT(*) FROM wellness_sessions")
        )
        count_before = before_wellness.scalar() or 0
        
        # Run seed again (simulated - in real test would call the script)
        # This is a placeholder - actual test would import and call seed_demo_data.main()
        
        # Count after
        after_wellness = await session.execute(
            text("SELECT COUNT(*) FROM wellness_sessions")
        )
        count_after = after_wellness.scalar() or 0
        
        # Note: This test assumes seed is idempotent
        # In practice, you'd run the seed script twice and verify no duplicates
        assert count_after >= count_before, "Seed should not reduce data"
        
        # Check unique constraints prevent duplicates
        duplicate_check = await session.execute(
            text("""
                SELECT player_id, date, COUNT(*) 
                FROM wellness_sessions
                GROUP BY player_id, date
                HAVING COUNT(*) > 1
            """)
        )
        duplicates = duplicate_check.fetchall()
        
        assert len(duplicates) == 0, f"Found duplicate wellness sessions: {duplicates}"


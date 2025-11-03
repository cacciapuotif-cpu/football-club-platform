"""
Seed script for demo data.
Creates 2 teams, 20 players, 1 match, 1 training session, sample data.
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import settings
from app.database import async_session_maker
from app.models.injury import Injury, InjurySeverity, InjuryType
from app.models.match import Attendance, Match, MatchResult, MatchType
from app.models.organization import Organization
from app.models.player import DominantFoot, Player, PlayerRole
from app.models.session import SessionType, TrainingSession
from app.models.team import Season, Team
from app.models.test import PhysicalTest, TechnicalTest, WellnessData
from app.models.user import User, UserRole
from app.security import get_password_hash


async def seed_data():
    """Seed demo data."""
    print("🌱 Seeding demo data...")

    async with async_session_maker() as session:
        # Create Organization
        org = Organization(
            id=uuid4(),
            name="ASD Calcio Demo",
            slug="asd-calcio-demo",
            email="info@asddemo.it",
            city="Milano",
            country="IT",
            benchmark_opt_in=True,
        )
        session.add(org)
        await session.flush()
        print(f"✅ Created organization: {org.name}")

        # Create Season
        season = Season(
            id=uuid4(),
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_active=True,
            organization_id=org.id,
        )
        session.add(season)
        await session.flush()

        # Create Users
        admin_user = User(
            id=uuid4(),
            email="admin@club1.local",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            organization_id=org.id,
        )
        session.add(admin_user)

        coach_user = User(
            id=uuid4(),
            email="coach@club1.local",
            hashed_password=get_password_hash("coach123"),
            full_name="Coach Mario",
            role=UserRole.COACH,
            is_active=True,
            is_verified=True,
            organization_id=org.id,
        )
        session.add(coach_user)

        # Create Team 1
        team1 = Team(
            id=uuid4(),
            name="Under 17",
            category="U17",
            season_id=season.id,
            organization_id=org.id,
        )
        session.add(team1)
        await session.flush()
        print(f"✅ Created team: {team1.name}")

        # Create Players
        players = []
        roles = [PlayerRole.GK, PlayerRole.DF, PlayerRole.DF, PlayerRole.DF, PlayerRole.MF, PlayerRole.MF, PlayerRole.MF, PlayerRole.FW, PlayerRole.FW, PlayerRole.FW]

        for i in range(10):
            player = Player(
                id=uuid4(),
                first_name=f"Player{i+1}",
                last_name=f"Demo{i+1}",
                date_of_birth=date(2007, 1 + i % 12, 15),
                nationality="IT",
                role_primary=roles[i],
                dominant_foot=DominantFoot.RIGHT if i % 2 == 0 else DominantFoot.LEFT,
                height_cm=170 + i * 2,
                weight_kg=65 + i,
                jersey_number=i + 1,
                consent_given=True,
                consent_date=datetime.now(),
                is_active=True,
                organization_id=org.id,
                team_id=team1.id,
            )
            session.add(player)
            players.append(player)

        await session.flush()
        print(f"✅ Created {len(players)} players")

        # Create Player User
        player_user = User(
            id=uuid4(),
            email="player1@club1.local",
            hashed_password=get_password_hash("player123"),
            full_name=f"{players[0].first_name} {players[0].last_name}",
            role=UserRole.PLAYER,
            is_active=True,
            is_verified=True,
            organization_id=org.id,
            player_id=players[0].id,
        )
        session.add(player_user)

        # Create Match
        match = Match(
            id=uuid4(),
            match_date=datetime.now() - timedelta(days=7),
            match_type=MatchType.LEAGUE,
            team_id=team1.id,
            opponent_name="FC Rivale",
            is_home=True,
            goals_for=2,
            goals_against=1,
            result=MatchResult.WIN,
            venue="Stadio Comunale",
            organization_id=org.id,
        )
        session.add(match)
        await session.flush()
        print(f"✅ Created match: {org.name} vs {match.opponent_name}")

        # Create Attendances
        for idx, player in enumerate(players[:8]):
            attendance = Attendance(
                id=uuid4(),
                match_id=match.id,
                player_id=player.id,
                is_starter=idx < 5,
                minutes_played=90 if idx < 5 else 45,
                coach_rating=6.5 + (idx * 0.2),
                organization_id=org.id,
            )
            session.add(attendance)

        # Create Training Session
        training = TrainingSession(
            id=uuid4(),
            session_date=datetime.now() - timedelta(days=2),
            session_type=SessionType.TRAINING,
            duration_min=90,
            team_id=team1.id,
            focus="Tecnico",
            description="Allenamento tecnico con focus su passaggi e controllo palla",
            planned_intensity=7,
            organization_id=org.id,
        )
        session.add(training)

        # Create Physical Tests
        for player in players[:5]:
            test = PhysicalTest(
                id=uuid4(),
                test_date=date.today() - timedelta(days=30),
                player_id=player.id,
                height_cm=player.height_cm,
                weight_kg=player.weight_kg,
                vo2max_ml_kg_min=52.0 + (hash(str(player.id)) % 10),
                sprint_10m_s=1.8 + (hash(str(player.id)) % 3) * 0.1,
                sprint_30m_s=4.2 + (hash(str(player.id)) % 5) * 0.1,
                cmj_cm=35.0 + (hash(str(player.id)) % 8),
                organization_id=org.id,
            )
            session.add(test)

        # Create Wellness Data
        for player in players[:8]:
            for days_ago in range(7):
                wellness = WellnessData(
                    id=uuid4(),
                    date=date.today() - timedelta(days=days_ago),
                    player_id=player.id,
                    sleep_hours=7.0 + (hash(str(player.id) + str(days_ago)) % 3) * 0.5,
                    sleep_quality=3 + (hash(str(player.id) + str(days_ago)) % 3),
                    hrv_ms=50.0 + (hash(str(player.id) + str(days_ago)) % 20),
                    fatigue_rating=2 + (hash(str(player.id) + str(days_ago)) % 3),
                    stress_rating=2 + (hash(str(player.id) + str(days_ago)) % 3),
                    mood_rating=3 + (hash(str(player.id) + str(days_ago)) % 3),
                    srpe=5 + (hash(str(player.id) + str(days_ago)) % 4),
                    organization_id=org.id,
                )
                session.add(wellness)

        # Create one Injury
        injury = Injury(
            id=uuid4(),
            player_id=players[3].id,
            injury_date=date.today() - timedelta(days=45),
            injury_type=InjuryType.MUSCLE,
            body_part="Hamstring",
            severity=InjurySeverity.MODERATE,
            expected_return_date=date.today() + timedelta(days=7),
            days_out=14,
            is_active=True,
            organization_id=org.id,
        )
        session.add(injury)

        await session.commit()
        print("✅ All demo data seeded successfully!")

        print("\n📋 Demo Credentials:")
        print("   Admin:  admin@club1.local / admin123")
        print("   Coach:  coach@club1.local / coach123")
        print("   Player: player1@club1.local / player123")
        print(f"\n🏢 Organization: {org.name} (slug: {org.slug})")
        print(f"⚽ Team: {team1.name} ({len(players)} players)")
        print(f"🏆 Match: {match.opponent_name} (Result: {match.result.value})")
        print(f"🏋️ Training Sessions: 1")
        print(f"📊 Wellness Records: {7 * 8}")


if __name__ == "__main__":
    asyncio.run(seed_data())

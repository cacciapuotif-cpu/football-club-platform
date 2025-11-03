#!/usr/bin/env python3
"""Seed script - 5 players (ages 15-19) with 5 training sessions each."""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add backend to path only if running outside container
try:
    import app
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, select
from sqlmodel import Session
from passlib.context import CryptContext

from app.config import settings
from app.models import (
    Organization, Season, Team, Player, TrainingSession, User
)
from app.models.player import PlayerRole, DominantFoot, DominantArm
from app.models.session import SessionType

database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
engine = create_engine(database_url, echo=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with Session(engine) as session:
    print("=== SEEDING 5 PLAYERS (AGES 15-19) WITH 5 SESSIONS EACH ===\n")

    # Get or create Organization
    org = session.exec(select(Organization).where(Organization.slug == "demo-fc")).first()
    if not org:
        org = Organization(
            id=uuid4(), name="Demo FC", slug="demo-fc",
            email="info@demofc.local", phone="+39 0123456789",
            address="Via dello Stadio, 1 - 00100 Roma RM",
            is_active=True
        )
        session.add(org)
        session.commit()
        session.refresh(org)
        print(f"✓ Created Organization: {org.name}")
    else:
        print(f"✓ Using existing Organization: {org.name}")

    # Get or create User
    user = session.exec(select(User).where(User.email == "admin@demofc.local")).first()
    if not user:
        user = User(
            id=uuid4(), email="admin@demofc.local",
            hashed_password=pwd_context.hash("demo123"),
            full_name="Demo Admin", is_active=True, is_superuser=True,
            organization_id=org.id
        )
        session.add(user)
        session.commit()
        print(f"✓ Created User: {user.email} / demo123")
    else:
        print(f"✓ Using existing User: {user.email}")

    # Get or create Season
    season = session.exec(
        select(Season).where(
            Season.organization_id == org.id,
            Season.name == "2024/2025"
        )
    ).first()
    if not season:
        season = Season(
            id=uuid4(), organization_id=org.id, name="2024/2025",
            start_date=date(2024, 8, 1), end_date=date(2025, 6, 30),
            is_active=True
        )
        session.add(season)
        session.commit()
        session.refresh(season)
        print(f"✓ Created Season: {season.name}")
    else:
        print(f"✓ Using existing Season: {season.name}")

    # Get or create Team
    team = session.exec(
        select(Team).where(
            Team.organization_id == org.id,
            Team.season_id == season.id,
            Team.name == "Giovanili"
        )
    ).first()
    if not team:
        team = Team(
            id=uuid4(), organization_id=org.id, season_id=season.id,
            name="Giovanili", category="Youth", is_active=True
        )
        session.add(team)
        session.commit()
        session.refresh(team)
        print(f"✓ Created Team: {team.name}")
    else:
        print(f"✓ Using existing Team: {team.name}")

    # Define 5 players with different ages
    today = date.today()
    players_data = [
        {
            "age": 15,
            "first_name": "Marco",
            "last_name": "Esposito",
            "birth_date": date(today.year - 15, 6, 20),
            "role_primary": PlayerRole.MF,
            "role_secondary": PlayerRole.FW,
            "jersey_number": 7,
            "height": 168,
            "weight": 62
        },
        {
            "age": 16,
            "first_name": "Luca",
            "last_name": "Bianchi",
            "birth_date": date(today.year - 16, 3, 15),
            "role_primary": PlayerRole.MF,
            "role_secondary": PlayerRole.FW,
            "jersey_number": 10,
            "height": 172,
            "weight": 65
        },
        {
            "age": 17,
            "first_name": "Matteo",
            "last_name": "Ferrari",
            "birth_date": date(today.year - 17, 9, 8),
            "role_primary": PlayerRole.DF,
            "role_secondary": PlayerRole.MF,
            "jersey_number": 4,
            "height": 175,
            "weight": 68
        },
        {
            "age": 18,
            "first_name": "Alessandro",
            "last_name": "Rossi",
            "birth_date": date(today.year - 18, 1, 8),
            "role_primary": PlayerRole.FW,
            "role_secondary": PlayerRole.MF,
            "jersey_number": 9,
            "height": 178,
            "weight": 72
        },
        {
            "age": 19,
            "first_name": "Giovanni",
            "last_name": "Romano",
            "birth_date": date(today.year - 19, 11, 25),
            "role_primary": PlayerRole.GK,
            "role_secondary": None,
            "jersey_number": 1,
            "height": 186,
            "weight": 78
        }
    ]

    # Create players
    print("\n=== Creating Players ===")
    created_players = []
    for data in players_data:
        # Check if player already exists
        existing = session.exec(
            select(Player).where(
                Player.first_name == data["first_name"],
                Player.last_name == data["last_name"],
                Player.organization_id == org.id
            )
        ).first()

        if existing:
            print(f"⚠ Player {data['first_name']} {data['last_name']} already exists, skipping...")
            created_players.append(existing)
            continue

        player = Player(
            id=uuid4(),
            organization_id=org.id,
            team_id=team.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["birth_date"],
            place_of_birth="Roma, IT",
            nationality="IT",
            role_primary=data["role_primary"],
            role_secondary=data["role_secondary"],
            dominant_foot=DominantFoot.RIGHT,
            dominant_arm=DominantArm.RIGHT,
            jersey_number=data["jersey_number"],
            height_cm=data["height"],
            weight_kg=data["weight"],
            bmi=round(data["weight"] / ((data["height"] / 100) ** 2), 1),
            is_minor=(data["age"] < 18),
            consent_given=True,
            consent_date=datetime.now(),
            medical_clearance=True,
            medical_clearance_expiry=date.today() + timedelta(days=365),
            is_active=True
        )
        session.add(player)
        session.flush()
        session.refresh(player)
        created_players.append(player)
        print(f"✓ Created: {player.first_name} {player.last_name} ({data['age']} years) - {player.role_primary.value}")

    session.commit()

    # Create 5 training sessions for each player
    print("\n=== Creating Training Sessions ===")
    session_types = [SessionType.TRAINING, SessionType.TACTICAL, SessionType.GYM,
                     SessionType.TRAINING, SessionType.FRIENDLY]

    for player in created_players:
        print(f"\n  Sessions for {player.first_name} {player.last_name}:")

        for i in range(5):
            session_date = datetime.now() - timedelta(days=20 - (i * 4))

            training_session = TrainingSession(
                id=uuid4(),
                organization_id=org.id,
                team_id=team.id,
                session_date=session_date,
                session_type=session_types[i],
                duration_min=90 if session_types[i] == SessionType.FRIENDLY else 75,
                focus="Allenamento tecnico" if i % 2 == 0 else "Allenamento tattico",
                description=f"Sessione di {session_types[i].value.lower()}",
                planned_intensity=7 + (i % 3),
                actual_intensity_avg=6.5 + (i * 0.3),
                distance_m=5000 + (i * 200),
                hi_distance_m=800 + (i * 50),
                sprints_count=12 + (i * 2),
                top_speed_ms=8.0 + (i * 0.2),
                hr_avg_bpm=145 + (i * 3),
                hr_max_bpm=175 + (i * 2)
            )
            session.add(training_session)
            print(f"    ✓ Session {i+1}: {session_date.strftime('%Y-%m-%d')} - {session_types[i].value}")

    session.commit()

    print("\n" + "="*60)
    print("✅ SEEDING COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   • Organization: {org.name}")
    print(f"   • Team: {team.name}")
    print(f"   • Season: {season.name}")
    print(f"   • Players created: {len(created_players)}")
    print(f"   • Training sessions created: {len(created_players) * 5}")
    print(f"\n🌐 Access the platform:")
    print(f"   • API: http://localhost:8000/docs")
    print(f"   • Frontend: http://localhost:3000/players")
    print(f"   • User: admin@demofc.local / demo123")
    print()

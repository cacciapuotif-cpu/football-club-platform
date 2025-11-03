#!/usr/bin/env python3
"""Simple seed script - essential data only."""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, select
from sqlmodel import Session
from passlib.context import CryptContext

from app.config import settings
from app.models import (
    Organization, Season, Team, Player, TrainingSession, User,
    PhysicalTest, WellnessData
)
from app.models.player import PlayerRole, DominantFoot, DominantArm
from app.models.session import SessionType

database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
engine = create_engine(database_url, echo=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with Session(engine) as session:
    print("Creating simple demo data...")

    # Organization
    org = Organization(
        id=uuid4(), name="Demo FC", slug="demo-fc",
        email="info@demofc.local", phone="+39 0123456789",
        address="Via dello Stadio, 1 - 00100 Roma RM",
        is_active=True
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    print(f"✓ Organization: {org.name}")

    # User
    user = User(
        id=uuid4(), email="admin@demofc.local",
        hashed_password=pwd_context.hash("demo123"),
        full_name="Demo Admin", is_active=True, is_superuser=True,
        organization_id=org.id
    )
    session.add(user)
    session.commit()
    print(f"✓ User: {user.email} / demo123")

    # Season
    season = Season(
        id=uuid4(), organization_id=org.id, name="2024/2025",
        start_date=date(2024, 8, 1), end_date=date(2025, 6, 30),
        is_active=True
    )
    session.add(season)
    session.commit()
    session.refresh(season)
    print(f"✓ Season: {season.name}")

    # Team
    team = Team(
        id=uuid4(), organization_id=org.id, season_id=season.id,
        name="Prima Squadra", category="Senior", is_active=True
    )
    session.add(team)
    session.commit()
    session.refresh(team)
    print(f"✓ Team: {team.name}")

    # Players
    players_data = [
        ("Mario", "Rossi", PlayerRole.GK, 1, 185, 78),
        ("Luca", "Bianchi", PlayerRole.GK, 12, 188, 82),
        ("Giuseppe", "Ferrari", PlayerRole.DF, 3, 180, 75),
        ("Antonio", "Russo", PlayerRole.DF, 4, 182, 77),
        ("Marco", "Romano", PlayerRole.DF, 5, 178, 73),
        ("Stefano", "Greco", PlayerRole.MF, 6, 176, 71),
        ("Andrea", "Bruno", PlayerRole.MF, 8, 175, 70),
        ("Matteo", "Gallo", PlayerRole.MF, 10, 177, 72),
        ("Simone", "Leone", PlayerRole.FW, 9, 181, 76),
        ("Riccardo", "Costa", PlayerRole.FW, 11, 179, 74),
    ]

    for first, last, role, jersey, height, weight in players_data:
        player = Player(
            id=uuid4(), organization_id=org.id, team_id=team.id,
            first_name=first, last_name=last,
            date_of_birth=date(1995, 1, 1), place_of_birth="Roma, IT",
            nationality="IT", role_primary=role, jersey_number=jersey,
            height_cm=height, weight_kg=weight,
            bmi=round(weight / ((height / 100) ** 2), 1),
            dominant_foot=DominantFoot.RIGHT, dominant_arm=DominantArm.RIGHT,
            consent_given=True, consent_date=datetime.now(),
            medical_clearance=True,
            medical_clearance_expiry=date.today() + timedelta(days=365),
            is_active=True
        )
        session.add(player)
        session.flush()

    session.commit()
    print(f"✓ Created {len(players_data)} players")

    # Get players for sessions
    players = session.exec(select(Player).where(Player.organization_id == org.id)).all()

    # Training Sessions
    for i in range(6):
        ts = TrainingSession(
            id=uuid4(), organization_id=org.id, team_id=team.id,
            session_date=datetime.now() - timedelta(days=7-i),
            session_type=SessionType.TRAINING, focus="Allenamento",
            duration_min=90, planned_intensity=7, actual_intensity_avg=7.5,
            distance_m=5000, hi_distance_m=800, sprints_count=15,
            top_speed_ms=8.5, hr_avg_bpm=150, hr_max_bpm=180
        )
        session.add(ts)
        session.flush()

    session.commit()
    print("✓ Created 6 training sessions")

    print("\n✅ SEED COMPLETED!")
    print(f"   Organization: {org.name}")
    print(f"   Team: {team.name}")
    print(f"   Players: {len(players)}")
    print(f"   User: {user.email} / demo123")

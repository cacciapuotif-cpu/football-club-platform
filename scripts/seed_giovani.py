#!/usr/bin/env python3
"""Script semplice per inserire 5 giocatori (15-19 anni) con 5 sessioni ciascuno."""

import sys
from datetime import date, datetime, timedelta
from uuid import uuid4

try:
    import app
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.config import settings
from app.models import Organization, Season, Team, Player, TrainingSession, User, SensorData
from app.models.player import PlayerRole, DominantFoot, DominantArm
from app.models.session import SessionType

database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
engine = create_engine(database_url, echo=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with Session(engine) as db:
    print("\n=== INSERIMENTO 5 GIOCATORI (15-19 ANNI) ===\n")

    # Usa o crea Organization
    org = db.exec(select(Organization).where(Organization.slug == "football_club_platform_academy")).first()
    if org:
        print(f"✓ Usando organizzazione esistente: {org.name}")
        org_id = org.id
    else:
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Football Club Platform Academy",
            slug="football_club_platform_academy",
            email="info@football_club_platform.local",
            is_active=True
        )
        db.add(org)
        db.commit()
        print(f"✓ Creata organizzazione: {org.name}")

    # Usa o crea User admin
    user = db.exec(select(User).where(User.email == "admin@football_club_platform.local")).first()
    if not user:
        user = User(
            id=uuid4(),
            email="admin@football_club_platform.local",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Amministratore",
            is_active=True,
            is_superuser=True,
            organization_id=org_id
        )
        db.add(user)
        db.commit()
        print(f"✓ Creato utente: {user.email} / admin123")
    else:
        print(f"✓ Usando utente esistente: {user.email}")

    # Usa o crea Season
    season = db.exec(select(Season).where(
        Season.organization_id == org_id,
        Season.name == "2024/2025"
    )).first()
    if not season:
        season = Season(
            id=uuid4(),
            organization_id=org_id,
            name="2024/2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_active=True
        )
        db.add(season)
        db.commit()
        print(f"✓ Creata stagione: {season.name}")
    else:
        print(f"✓ Usando stagione esistente: {season.name}")

    # Usa o crea Team
    team = db.exec(select(Team).where(
        Team.organization_id == org_id,
        Team.season_id == season.id,
        Team.name == "Giovanili Football Club Platform"
    )).first()
    if not team:
        team = Team(
            id=uuid4(),
            organization_id=org_id,
            season_id=season.id,
            name="Giovanili Football Club Platform",
            category="Youth",
            is_active=True
        )
        db.add(team)
        db.commit()
        print(f"✓ Creato team: {team.name}\n")
    else:
        print(f"✓ Usando team esistente: {team.name}\n")

    # Dati giocatori
    today = date.today()
    players_info = [
        ("Marco", "Esposito", 15, PlayerRole.MF, 7, 168, 62),
        ("Luca", "Bianchi", 16, PlayerRole.MF, 10, 172, 65),
        ("Matteo", "Ferrari", 17, PlayerRole.DF, 4, 175, 68),
        ("Alessandro", "Rossi", 18, PlayerRole.FW, 9, 178, 72),
        ("Giovanni", "Romano", 19, PlayerRole.GK, 1, 186, 78)
    ]

    print("=== GIOCATORI ===")
    players = []
    for first, last, age, role, jersey, height, weight in players_info:
        birth_date = date(today.year - age, 6, 15)

        player = Player(
            id=uuid4(),
            organization_id=org_id,
            team_id=team.id,
            first_name=first,
            last_name=last,
            date_of_birth=birth_date,
            place_of_birth="Roma, IT",
            nationality="IT",
            role_primary=role,
            dominant_foot=DominantFoot.RIGHT,
            dominant_arm=DominantArm.RIGHT,
            jersey_number=jersey,
            height_cm=height,
            weight_kg=weight,
            bmi=round(weight / ((height / 100) ** 2), 1),
            is_minor=(age < 18),
            consent_given=True,
            consent_date=datetime.now(),
            medical_clearance=True,
            medical_clearance_expiry=today + timedelta(days=365),
            is_active=True
        )
        db.add(player)
        db.flush()
        players.append(player)
        print(f"  ✓ {first} {last} ({age} anni) - {role.value} #{jersey}")

    db.commit()
    print(f"\n✓ Totale giocatori: {len(players)}\n")

    # Crea 5 sessioni DIVERSE per ogni giocatore (25 sessioni totali)
    print("=== SESSIONI DI ALLENAMENTO INDIVIDUALI ===")
    session_types = [SessionType.TRAINING, SessionType.TACTICAL, SessionType.GYM,
                     SessionType.TRAINING, SessionType.FRIENDLY]

    total_sessions = 0
    total_sensor_data = 0

    for idx, player in enumerate(players):
        player_name = players_info[idx][0] + " " + players_info[idx][1]
        print(f"\n  Sessioni per {player_name}:")

        for i in range(5):
            # Ogni giocatore ha sessioni in date diverse (sfalsate per giocatore)
            session_date = datetime.now() - timedelta(days=20 - (i * 4) + (idx * 1))
            session_id = uuid4()
            duration = 90 if session_types[i] == SessionType.FRIENDLY else 75

            # Crea la sessione di allenamento
            training = TrainingSession(
                id=session_id,
                organization_id=org_id,
                team_id=team.id,
                session_date=session_date,
                session_type=session_types[i],
                duration_min=duration,
                focus="Tecnica" if i % 2 == 0 else "Tattica",
                planned_intensity=6 + i,
                actual_intensity_avg=6.0 + (i * 0.4) + (idx * 0.1),
                distance_m=5000 + (i * 200) + (idx * 100),
                hi_distance_m=800 + (i * 50) + (idx * 20),
                sprints_count=10 + (i * 2) + idx,
                top_speed_ms=7.5 + (i * 0.3) + (idx * 0.2),
                hr_avg_bpm=145 + (i * 3) + (idx * 2),
                hr_max_bpm=175 + (i * 2) + (idx * 3)
            )
            db.add(training)
            db.commit()
            total_sessions += 1

            # Crea i dati del sensore per il giocatore
            sensor = SensorData(
                id=uuid4(),
                player_id=player.id,
                session_id=session_id,
                timestamp=session_date,
                duration_sec=duration * 60,
                distance_m=5000 + (i * 200) + (idx * 100),
                distance_km=round((5000 + (i * 200) + (idx * 100)) / 1000, 2),
                sprint_count=10 + (i * 2) + idx,
                top_speed_km_h=round((7.5 + (i * 0.3) + (idx * 0.2)) * 3.6, 1),
                accelerations=25 + (i * 3) + idx,
                decelerations=20 + (i * 2) + idx,
                player_load=round(350 + (i * 20) + (idx * 10), 1),
                hr_avg_bpm=145 + (i * 3) + (idx * 2),
                hr_peak_bpm=175 + (i * 2) + (idx * 3),
                data_source="Football Club Platform Tracker",
                organization_id=org_id
            )
            db.add(sensor)
            db.commit()
            total_sensor_data += 1

            print(f"    ✓ {session_date.strftime('%d/%m/%Y')} - {session_types[i].value}")

    print("\n" + "="*60)
    print("✅ COMPLETATO CON SUCCESSO!")
    print("="*60)
    print(f"\n📊 Riepilogo:")
    print(f"   • Organizzazione: {org.name}")
    print(f"   • Team: {team.name}")
    print(f"   • Giocatori inseriti: {len(players)}")
    print(f"   • Sessioni inserite (totali): {total_sessions}")
    print(f"   • Dati sensore inseriti: {total_sensor_data}")
    print(f"   • Sessioni per giocatore: {total_sessions // len(players)}")
    print(f"\n🌐 Accedi alla piattaforma:")
    print(f"   • Backend API: http://localhost:8000/docs")
    print(f"   • Frontend: http://localhost:3000/players")
    print(f"   • Login: admin@football_club_platform.local / admin123\n")

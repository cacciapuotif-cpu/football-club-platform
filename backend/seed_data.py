"""Seed script to populate database with sample data directly."""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4
from sqlmodel import select
from app.database import get_session_context
from app.models.organization import Organization
from app.models.team import Team, Season
from app.models.player import Player
from app.models.session import TrainingSession
from app.models.wellness import WellnessData

def calculate_birth_date(age):
    """Calculate birth date from age."""
    today = datetime.now()
    birth_year = today.year - age
    return datetime(birth_year, 1, 15).date()

async def seed_database():
    """Seed the database with sample data."""
    print("=" * 60)
    print("Football Club Platform - Seeding Database")
    print("=" * 60)
    print()

    async with get_session_context() as session:
        # Get the organization (should exist from quick_setup)
        print(">> Finding organization...")
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()

        if not org:
            print("[ERROR] No organization found. Run quick_setup.py first!")
            return

        print(f"[OK] Found organization: {org.name}")
        org_id = org.id

        # Create Season
        print("\n>> Creating season...")
        current_year = datetime.now().year
        season = Season(
            id=uuid4(),
            name=f"Stagione {current_year}/{current_year+1}",
            start_date=datetime(current_year, 9, 1).date(),
            end_date=datetime(current_year+1, 6, 30).date(),
            is_active=True,
            organization_id=org_id
        )
        session.add(season)
        await session.commit()
        await session.refresh(season)
        print(f"[OK] Created season: {season.name}")

        # Create Team
        print("\n>> Creating team...")
        team = Team(
            id=uuid4(),
            name="Juniores U19",
            category="U19",
            season_id=season.id,
            organization_id=org_id
        )
        session.add(team)
        await session.commit()
        await session.refresh(team)
        print(f"[OK] Created team: {team.name}")

        # Create Player 1 (17 years old)
        print("\n>> Creating players...")
        player1 = Player(
            id=uuid4(),
            first_name="Marco",
            last_name="Rossi",
            date_of_birth=calculate_birth_date(17),
            place_of_birth="Milano",
            nationality="IT",
            role_primary="FW",
            dominant_foot="RIGHT",
            jersey_number=10,
            height_cm=175.0,
            weight_kg=68.0,
            is_active=True,
            is_minor=True,
            guardian_name="Giuseppe Rossi",
            guardian_email="giuseppe.rossi@email.it",
            guardian_phone="+39 320 1234567",
            consent_given=True,
            consent_date=datetime.now(),
            organization_id=org_id
        )
        session.add(player1)
        await session.commit()
        await session.refresh(player1)
        print(f"[OK] Created player: Marco Rossi (17 anni)")

        # Create Player 2 (18 years old)
        player2 = Player(
            id=uuid4(),
            first_name="Luca",
            last_name="Bianchi",
            date_of_birth=calculate_birth_date(18),
            place_of_birth="Roma",
            nationality="IT",
            role_primary="MF",
            dominant_foot="LEFT",
            jersey_number=8,
            height_cm=180.0,
            weight_kg=73.0,
            is_active=True,
            is_minor=False,
            email="luca.bianchi@email.it",
            phone="+39 340 7654321",
            consent_given=True,
            consent_date=datetime.now(),
            organization_id=org_id
        )
        session.add(player2)
        await session.commit()
        await session.refresh(player2)
        print(f"[OK] Created player: Luca Bianchi (18 anni)")

        # Create 10 training sessions
        print("\n>> Creating training sessions...")

        session_types = ["TRAINING", "TRAINING", "TRAINING", "GYM", "TACTICAL", "TRAINING", "FRIENDLY", "RECOVERY", "TRAINING", "TRAINING"]
        focuses = [
            "Lavoro tecnico sui passaggi",
            "Esercizi di resistenza e velocità",
            "Tattica difensiva e pressing",
            "Potenziamento muscolare",
            "Schema 4-3-3 e movimenti offensivi",
            "Possesso palla e transizioni",
            "Partita amichevole vs Juniores",
            "Recupero attivo e stretching",
            "Tiri in porta e finalizzazione",
            "Gioco posizionale e pressing alto"
        ]

        intensities = [7, 8, 6, 9, 5, 7, 8, 3, 8, 7]
        durations = [90, 90, 75, 60, 90, 90, 90, 45, 75, 90]

        sessions_created = 0
        for i in range(10):
            session_date = datetime.now() - timedelta(days=(9 - i) * 2)

            training_session = TrainingSession(
                id=uuid4(),
                session_date=session_date,
                session_type=session_types[i],
                duration_min=durations[i],
                team_id=team.id,
                focus=focuses[i],
                planned_intensity=intensities[i],
                description=f"Sessione {i+1}: {focuses[i]}",
                organization_id=org_id
            )
            session.add(training_session)
            await session.commit()
            sessions_created += 1

        print(f"[OK] Created {sessions_created} training sessions")

        # Create wellness data for both players (last 14 days for ML predictions)
        print("\n>> Creating wellness data for ML predictions...")
        wellness_created = 0

        for player in [player1, player2]:
            for day_offset in range(14):
                wellness_date = (datetime.now() - timedelta(days=13 - day_offset)).date()

                # Generate realistic wellness data with some variation
                base_sleep = random.uniform(7.0, 8.5)
                base_hrv = random.uniform(55, 75)
                base_hr = random.randint(50, 65)

                # Add variation based on training load
                if day_offset % 3 == 0:  # Recovery days
                    sleep_hours = base_sleep + random.uniform(0, 0.5)
                    hrv_ms = base_hrv + random.uniform(5, 15)
                    doms = random.randint(1, 2)
                    fatigue = random.randint(1, 2)
                    training_load = random.randint(200, 350)
                else:  # Training days
                    sleep_hours = base_sleep - random.uniform(0, 0.5)
                    hrv_ms = base_hrv - random.uniform(0, 10)
                    doms = random.randint(2, 4)
                    fatigue = random.randint(2, 4)
                    training_load = random.randint(400, 650)

                wellness = WellnessData(
                    id=uuid4(),
                    player_id=player.id,
                    date=wellness_date,
                    sleep_hours=round(sleep_hours, 1),
                    sleep_quality=random.randint(3, 5),
                    resting_hr_bpm=base_hr + random.randint(-5, 5),
                    hrv_ms=round(hrv_ms, 1),
                    doms_rating=doms,
                    fatigue_rating=fatigue,
                    stress_rating=random.randint(1, 3),
                    mood_rating=random.randint(6, 9),
                    training_load=training_load,
                    notes=f"Dati giornalieri {wellness_date}",
                    organization_id=org_id
                )
                session.add(wellness)
                wellness_created += 1

        await session.commit()
        print(f"[OK] Created {wellness_created} wellness data entries (14 days × 2 players)")

    print()
    print("=" * 60)
    print("[SUCCESS] Database seeded successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Created season: Stagione {current_year}/{current_year+1}")
    print(f"  - Created team: Juniores U19")
    print(f"  - Created 2 players:")
    print(f"    • Marco Rossi (17 anni) - Attaccante #10")
    print(f"    • Luca Bianchi (18 anni) - Centrocampista #8")
    print(f"  - Created 10 training sessions")
    print(f"  - Created {wellness_created} wellness data entries for ML predictions")
    print()
    print("You can now view and test:")
    print("  - Players: http://localhost:3000/players")
    print("  - Sessions: http://localhost:3000/sessions")
    print("  - ML Reports API: http://localhost:8000/docs#/ML%20Reports%20%26%20Predictions")
    print()
    print("Test ML predictions with:")
    print(f"  GET /api/v1/ml/report/{{player_id}}")
    print(f"  GET /api/v1/ml/predict/performance/{{player_id}}")
    print(f"  GET /api/v1/ml/predict/injury-risk/{{player_id}}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(seed_database())

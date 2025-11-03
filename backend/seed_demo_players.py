"""
Seed Script - Dati Demo per Football Club Platform
====================================================
Crea 5 giocatori giovani (15-19 anni) con:
- 5 sessioni wellness per giocatore
- 10 sessioni di allenamento per giocatore
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.player import Player
from app.models.sensor import SensorData
from app.models.test import WellnessData
from app.models.organization import Organization


async def seed_demo_data():
    """Seed database with demo players and their data."""

    print("=" * 80)
    print("🌱 SEEDING DATABASE - Football Club Platform")
    print("=" * 80)

    async for session in get_session():
        try:
            # Truncate all tables with CASCADE to respect foreign keys
            print("🗑️  Cleaning existing data...")

            # Truncate using raw SQL with CASCADE
            await session.execute(text("TRUNCATE TABLE sensor_data, wellness_data, training_sessions, players, organizations CASCADE"))
            await session.commit()

            print("✅ Existing data cleaned!\n")

            # Create or get default organization
            print("🏢 Creating default organization...")
            org = Organization(
                name="Football Club Platform Demo",
                slug="football-club-platform-demo",
                email="demo@footballclubplatform.com",
                is_active=True,
            )
            session.add(org)
            await session.flush()
            print(f"✅ Organization created: {org.name} (ID: {org.id})\n")

            # Create 5 players (15-19 years old)
            # Roles: GK (Goalkeeper), DF (Defender), MF (Midfielder), FW (Forward)
            players_data = [
                {
                    "first_name": "Marco",
                    "last_name": "Rossi",
                    "date_of_birth": datetime.now() - timedelta(days=365*15 + 120),  # 15y 4m
                    "role_primary": "FW",  # Forward/Attaccante
                    "jersey_number": 9,
                },
                {
                    "first_name": "Luca",
                    "last_name": "Bianchi",
                    "date_of_birth": datetime.now() - timedelta(days=365*16 + 45),  # 16y 1.5m
                    "role_primary": "MF",  # Midfielder/Centrocampista
                    "jersey_number": 8,
                },
                {
                    "first_name": "Alessandro",
                    "last_name": "Verdi",
                    "date_of_birth": datetime.now() - timedelta(days=365*17 + 200),  # 17y 6m
                    "role_primary": "DF",  # Defender/Difensore
                    "jersey_number": 5,
                },
                {
                    "first_name": "Davide",
                    "last_name": "Neri",
                    "date_of_birth": datetime.now() - timedelta(days=365*18 + 90),  # 18y 3m
                    "role_primary": "GK",  # Goalkeeper/Portiere
                    "jersey_number": 1,
                },
                {
                    "first_name": "Matteo",
                    "last_name": "Gialli",
                    "date_of_birth": datetime.now() - timedelta(days=365*19 + 10),  # 19y 10d
                    "role_primary": "FW",  # Forward/Attaccante
                    "jersey_number": 7,
                },
            ]

            created_players = []
            print(f"\n📋 Creating {len(players_data)} players...")

            for idx, pdata in enumerate(players_data, 1):
                role_name = {"FW": "Attaccante", "MF": "Centrocampista", "DF": "Difensore", "GK": "Portiere"}[pdata["role_primary"]]

                player = Player(
                    first_name=pdata["first_name"],
                    last_name=pdata["last_name"],
                    date_of_birth=pdata["date_of_birth"],
                    role_primary=pdata["role_primary"],
                    jersey_number=pdata["jersey_number"],
                    height_cm=170 + idx * 3,  # 173-185cm
                    weight_kg=65 + idx * 2,   # 67-75kg
                    organization_id=org.id,
                    is_active=True,
                )
                session.add(player)
                await session.flush()  # Get player ID
                created_players.append(player)

                age = (datetime.now() - player.date_of_birth).days // 365
                print(f"   ✓ Player {idx}/5: {player.first_name} {player.last_name} "
                      f"(#{player.jersey_number}, {age} anni, {role_name})")

            await session.commit()
            print(f"✅ {len(created_players)} players created successfully!\n")

            # Create wellness data (5 per player)
            print(f"💪 Creating wellness data (5 entries per player)...")
            wellness_count = 0

            for player_idx, player in enumerate(created_players):
                for day_offset in range(5):
                    # Create wellness data for last 5 days
                    wellness_date = datetime.now() - timedelta(days=day_offset)

                    # Vary data slightly per player
                    base_sleep = 7.5 - (day_offset * 0.2)
                    base_fatigue = 3 + day_offset
                    base_mood = 4 - (day_offset * 0.3)

                    wellness = WellnessData(
                        player_id=player.id,
                        organization_id=org.id,
                        date=wellness_date.date(),
                        sleep_hours=max(6.0, min(9.0, base_sleep + (player_idx % 3) * 0.3)),
                        sleep_quality=max(1, min(5, 4 - day_offset // 2)),
                        fatigue_rating=max(1, min(5, int(base_fatigue))),
                        stress_rating=max(1, min(5, 3 + day_offset // 3)),
                        doms_rating=max(1, min(5, 2 + day_offset // 2)),
                        mood_rating=max(1, min(5, int(base_mood + 1))),
                        notes=f"Wellness check giorno {5-day_offset}" if day_offset < 3 else None,
                    )
                    session.add(wellness)
                    await session.flush()  # Flush each record immediately
                    wellness_count += 1

            await session.commit()
            print(f"✅ {wellness_count} wellness entries created!\n")

            # Create sensor/training data (10 per player)
            print(f"🏃 Creating training sessions data (10 per player)...")
            session_count = 0

            session_types = [
                ("Allenamento tecnico", 75),
                ("Allenamento tattico", 70),
                ("Allenamento fisico", 85),
                ("Partitella", 80),
                ("Lavoro aerobico", 65),
                ("Forza e potenza", 75),
                ("Rapidità e agilità", 80),
                ("Possesso palla", 70),
                ("Tiri in porta", 75),
                ("Recupero attivo", 50),
            ]

            for player_idx, player in enumerate(created_players):
                for idx, (title, duration) in enumerate(session_types):
                    # Create sessions for last 10 days
                    session_timestamp = datetime.now() - timedelta(days=idx)

                    # Vary metrics based on session type and player
                    base_distance = 5000 + (idx * 200) + (player_idx * 100)
                    base_hr = 145 + (idx * 3) + (player_idx * 2)

                    sensor_data = SensorData(
                        player_id=player.id,
                        session_id=None,  # Individual session, not team-based
                        timestamp=session_timestamp,
                        duration_sec=duration * 60,
                        distance_m=base_distance,
                        distance_km=round(base_distance / 1000, 2),
                        sprint_count=max(0, 15 - idx),
                        top_speed_km_h=round(27.0 + (player_idx * 0.5) - (idx * 0.3), 1),
                        accelerations=25 + idx + player_idx,
                        decelerations=20 + idx,
                        player_load=round(350.0 + (idx * 20) + (player_idx * 10), 1),
                        hr_avg_bpm=base_hr,
                        hr_peak_bpm=min(200, base_hr + 30),
                        data_source="Football Club Platform Demo",
                        organization_id=org.id,
                    )
                    session.add(sensor_data)
                    await session.flush()  # Flush each record immediately
                    session_count += 1

            await session.commit()
            print(f"✅ {session_count} training session records created!\n")

            # Final summary
            print("=" * 80)
            print("✅ SEED COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"\n📊 Summary:")
            print(f"   👥 Players:          {len(created_players)}")
            print(f"   💪 Wellness entries: {wellness_count}")
            print(f"   🏃 Training sessions: {session_count}")
            print(f"\n🎯 Total records:     {len(created_players) + wellness_count + session_count}")
            print("\n" + "=" * 80)

        except Exception as e:
            print(f"\n❌ ERROR during seed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    print("\n🚀 Starting seed process...")
    asyncio.run(seed_demo_data())
    print("✅ Seed script completed!\n")

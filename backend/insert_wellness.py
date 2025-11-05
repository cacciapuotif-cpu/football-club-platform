"""
Insert wellness data for test players.
Covers Oct 25 - Nov 4, 2025 (11 days) for 5 players.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID, uuid4
from sqlalchemy import text
from app.database import get_session_context

# Organization and team IDs from test data
ORG_ID = "d1ff8112-b2f6-4efa-b530-2e6d6ff6fc21"

# Player external IDs
PLAYERS = [
    "demo-fc-ps-1",   # Giuseppe Verdi, GK, #1
    "demo-fc-ps-5",   # Alessandro Ferrari, DF, #5
    "demo-fc-ps-7",   # Luca Bianchi, MF, #7
    "demo-fc-ps-9",   # Matteo Colombo, FW, #9
    "demo-fc-ps-10",  # Marco Rossi, FW, #10
]

# Date range
START_DATE = date(2025, 10, 25)
DAYS = 11

# Training intensity mapping (for training load correlation)
TRAINING_DAYS = {
    date(2025, 11, 4): "HIGH",    # TACTICAL
    date(2025, 11, 3): "MEDIUM",  # PHYSICAL
    date(2025, 11, 1): "MEDIUM",  # TRAINING
    date(2025, 10, 31): "LOW",    # RECOVERY
    date(2025, 10, 29): "MEDIUM", # TECHNICAL
    date(2025, 10, 28): "HIGH",   # PHYSICAL
    date(2025, 10, 26): "MEDIUM", # TACTICAL
    date(2025, 10, 25): "HIGH",   # TRAINING
}


async def insert_wellness_data():
    """Insert wellness data for all players."""

    async with get_session_context() as session:
        try:
            # Get player IDs
            result = await session.execute(
                text("SELECT id, external_id, first_name, last_name FROM players WHERE external_id = ANY(:ids)"),
                {"ids": PLAYERS}
            )
            players = result.fetchall()

            if not players:
                print("❌ No players found!")
                return

            print(f"✅ Found {len(players)} players")

            inserted_count = 0

            for player in players:
                player_id = str(player[0])
                external_id = player[1]
                name = f"{player[2]} {player[3]}"

                print(f"\n📊 Inserting wellness data for {name} ({external_id})")

                for day_offset in range(DAYS):
                    wellness_date = START_DATE + timedelta(days=day_offset)

                    # Determine training intensity for the day
                    intensity = TRAINING_DAYS.get(wellness_date, None)

                    # Base metrics (vary by player and day)
                    base_sleep = 7.5 + (day_offset % 3) * 0.3  # Varies 7.5-8.4h
                    base_weight = 72.0 + (PLAYERS.index(external_id) * 2)  # Different per player
                    base_hrv = 60 + (day_offset % 5) * 5  # Varies 60-80ms
                    base_hr = 55 + (day_offset % 4) * 2  # Varies 55-61bpm

                    # Subjective ratings (1-10, correlated with training intensity)
                    if intensity == "HIGH":
                        # High training day: more fatigue, more DOMS
                        doms = 6 + (day_offset % 3)
                        fatigue = 6 + (day_offset % 3)
                        stress = 5 + (day_offset % 3)
                        mood = 6 + (day_offset % 2)
                        motivation = 7 + (day_offset % 2)
                        hydration = 7
                        srpe = 8
                        session_duration = 90
                        training_load = srpe * session_duration
                    elif intensity == "MEDIUM":
                        # Medium training day: moderate levels
                        doms = 4 + (day_offset % 2)
                        fatigue = 4 + (day_offset % 2)
                        stress = 4 + (day_offset % 2)
                        mood = 7 + (day_offset % 2)
                        motivation = 7 + (day_offset % 2)
                        hydration = 8
                        srpe = 5
                        session_duration = 85
                        training_load = srpe * session_duration
                    elif intensity == "LOW":
                        # Recovery day: low fatigue
                        doms = 2 + (day_offset % 2)
                        fatigue = 3 + (day_offset % 2)
                        stress = 3
                        mood = 8
                        motivation = 7
                        hydration = 8
                        srpe = 3
                        session_duration = 45
                        training_load = srpe * session_duration
                    else:
                        # Rest day: best ratings
                        doms = 2
                        fatigue = 2
                        stress = 2
                        mood = 8 + (day_offset % 2)
                        motivation = 8 + (day_offset % 2)
                        hydration = 9
                        srpe = None
                        session_duration = None
                        training_load = None

                    # Sleep quality (1-5, inverse of fatigue)
                    sleep_quality = max(1, min(5, 6 - (fatigue // 2)))

                    # Insert wellness record
                    insert_query = text("""
                        INSERT INTO wellness_data (
                            id, player_id, organization_id, date,
                            sleep_hours, sleep_quality, sleep_start_hhmm, wake_time_hhmm,
                            body_weight_kg, hrv_ms, resting_hr_bpm,
                            doms_rating, fatigue_rating, stress_rating,
                            mood_rating, motivation_rating, hydration_rating,
                            srpe, session_duration_min, training_load,
                            notes
                        ) VALUES (
                            :id, :player_id, :org_id, :wellness_date,
                            :sleep_hours, :sleep_quality, :sleep_start, :wake_time,
                            :weight, :hrv, :hr,
                            :doms, :fatigue, :stress,
                            :mood, :motivation, :hydration,
                            :srpe, :duration, :load,
                            :notes
                        )
                    """)

                    await session.execute(insert_query, {
                        "id": str(uuid4()),
                        "player_id": player_id,
                        "org_id": ORG_ID,
                        "wellness_date": wellness_date,
                        "sleep_hours": round(base_sleep, 1),
                        "sleep_quality": sleep_quality,
                        "sleep_start": "2330",
                        "wake_time": "0730",
                        "weight": round(base_weight + (day_offset % 3) * 0.2, 1),
                        "hrv": base_hrv,
                        "hr": base_hr,
                        "doms": doms,
                        "fatigue": fatigue,
                        "stress": stress,
                        "mood": mood,
                        "motivation": motivation,
                        "hydration": hydration,
                        "srpe": srpe,
                        "duration": session_duration,
                        "load": training_load,
                        "notes": f"Wellness for {wellness_date} - {'Training day' if intensity else 'Rest day'}"
                    })

                    inserted_count += 1

            await session.commit()
            print(f"\n✅ Successfully inserted {inserted_count} wellness records")

            # Verify
            result = await session.execute(
                text("SELECT COUNT(*) FROM wellness_data WHERE organization_id = :org_id"),
                {"org_id": ORG_ID}
            )
            total = result.scalar()
            print(f"📊 Total wellness records in database: {total}")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(insert_wellness_data())

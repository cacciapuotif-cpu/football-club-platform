"""Seed script for ML analytics with realistic data (UUID + organization_id)."""

import random
from datetime import date, timedelta
from uuid import uuid4
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db_sync import get_db_context, engine_sync
from app.models.analytics import (
    Match,
    TrainingSession,
    PlayerMatchStat,
    PlayerTrainingLoad,
    PlayerFeatureDaily,
    Base,
)
from app.services.ml_analytics_service import train_all

random.seed(42)

# Fixed organization_id for testing
ORG_ID = uuid4()

# Named players with roles
NAMED_PLAYERS = [
    ("Luca", "Bianchi", "MF"),
    ("Francesco", "Gialli", "GK"),
    ("Andrea", "Neri", "MF"),
    ("Marco", "Rossi", "FW"),
    ("Giovanni", "Verdi", "DF"),
]


def role_profile(role: str):
    """Get statistical profile based on role."""
    if role == "FW":
        return dict(xg=0.35, shots=3, key_passes=2, duels=5, sprints=18)
    if role == "MF":
        return dict(xg=0.15, shots=1, key_passes=3, duels=7, sprints=12)
    if role == "DF":
        return dict(xg=0.05, shots=0, key_passes=1, duels=9, sprints=8)
    return dict(xg=0.01, shots=0, key_passes=0, duels=3, sprints=3)  # GK


def ensure_players():
    """Ensure named players exist."""
    with get_db_context() as db:
        # Check if players exist
        existing = db.execute("SELECT COUNT(*) FROM players").scalar()

        if existing < 5:
            print(f"Creating {5 - (existing or 0)} named players...")
            for first_name, last_name, role in NAMED_PLAYERS:
                player_id = uuid4()
                db.execute(
                    """
                    INSERT INTO players (id, first_name, last_name, role_primary, organization_id,
                                       date_of_birth, consent_given, medical_clearance, is_active)
                    VALUES (:id, :first_name, :last_name, :role, :org_id, :dob, true, true, true)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    {
                        "id": player_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": role,
                        "org_id": ORG_ID,
                        "dob": date(2000, 1, 1) + timedelta(days=random.randint(0, 3650)),
                    },
                )
            db.commit()
            print(f"Created players")

        # Get all player IDs
        rows = db.execute(
            "SELECT id, role_primary FROM players WHERE is_active = true ORDER BY id LIMIT 10"
        ).fetchall()
        return [(r[0], r[1] or "MF") for r in rows]


def seed_matches(player_ids, start_date: date, end_date: date):
    """Seed match data."""
    with get_db_context() as db:
        print("Seeding matches...")
        days = (end_date - start_date).days
        match_count = 0

        for d in range(0, days, 7):  # 1 match per week
            match = Match(
                organization_id=ORG_ID,
                date=start_date + timedelta(days=d),
                opponent=f"Opponent-{random.randint(1, 20)}",
                competition="League",
                home=bool(random.getrandbits(1)),
                minutes=90,
            )
            db.add(match)
            db.flush()

            # Add player stats for this match
            for pid, role in player_ids:
                prof = role_profile(role)
                stat = PlayerMatchStat(
                    organization_id=ORG_ID,
                    player_id=pid,
                    match_id=match.id,
                    minutes=90,
                    goals=1 if (role == "FW" and random.random() < 0.3) else 0,
                    assists=1 if random.random() < 0.15 else 0,
                    shots=max(0, int(random.gauss(prof["shots"], 1))),
                    xg=max(0, round(random.gauss(prof["xg"], 0.1), 3)),
                    key_passes=max(0, int(random.gauss(prof["key_passes"], 1))),
                    duels_won=max(0, int(random.gauss(prof["duels"], 2))),
                    sprints=max(0, int(random.gauss(prof["sprints"], 4))),
                    pressures=max(0, int(random.gauss(10, 3))),
                    def_actions=max(0, int(random.gauss(8 if role in ("DF", "MF") else 3, 2))),
                )
                db.add(stat)

            match_count += 1

        db.commit()
        print(f"Created {match_count} matches")


def seed_sessions(player_ids, start_date: date, end_date: date):
    """Seed training sessions."""
    with get_db_context() as db:
        print("Seeding training sessions...")
        cur = start_date
        session_count = 0

        while cur <= end_date:
            if cur.weekday() in (0, 1, 3, 4):  # 4 sessions per week
                sess = TrainingSession(
                    organization_id=ORG_ID,
                    date=cur,
                    session_type=random.choice(["strength", "endurance", "tactical", "mixed"]),
                    duration_min=random.randint(60, 110),
                    rpe=round(random.uniform(4.0, 7.5), 2),
                )
                db.add(sess)
                db.flush()

                # Add player loads
                for pid, _ in player_ids:
                    ac = round(random.uniform(200, 800), 1)
                    ch = round(random.uniform(300, 900), 1)
                    mono = round(random.uniform(1.0, 3.0), 2)
                    strain = round(ac * mono, 2)

                    load = PlayerTrainingLoad(
                        organization_id=ORG_ID,
                        player_id=pid,
                        session_id=sess.id,
                        load_acute=ac,
                        load_chronic=ch,
                        monotony=mono,
                        strain=strain,
                        injury_history_flag=bool(random.random() < 0.1),
                    )
                    db.add(load)

                session_count += 1

            cur += timedelta(days=1)

        db.commit()
        print(f"Created {session_count} training sessions")


def seed_features_daily(player_ids, start_date: date, end_date: date):
    """Seed daily player features."""
    with get_db_context() as db:
        print("Seeding daily features...")
        feature_count = 0

        for pid, _ in player_ids:
            cur = start_date
            r7 = 0.0
            r21 = 0.0

            while cur <= end_date:
                r7 = max(0.0, r7 + random.uniform(-10, 10))
                r21 = max(0.0, r21 + random.uniform(-5, 15))
                form = max(0.0, min(1.0, random.gauss(0.5, 0.2)))

                feat = PlayerFeatureDaily(
                    organization_id=ORG_ID,
                    player_id=pid,
                    date=cur,
                    rolling_7d_load=round(r7, 2),
                    rolling_21d_load=round(r21, 2),
                    form_score=round(form, 3),
                    injury_flag=bool(random.random() < 0.05),
                )
                db.add(feat)
                feature_count += 1
                cur += timedelta(days=1)

        db.commit()
        print(f"Created {feature_count} daily feature records")


def main():
    """Main seed function."""
    print("=" * 60)
    print("ML Analytics Seed Script (UUID + Org)")
    print("=" * 60)

    # Create tables
    Base.metadata.create_all(bind=engine_sync)

    # Get players
    player_ids = ensure_players()
    print(f"Using {len(player_ids)} players")

    # Date range: last 2 months
    end = date.today()
    start = end - timedelta(days=60)
    print(f"Date range: {start} to {end}")

    # Seed data
    seed_matches(player_ids, start, end)
    seed_sessions(player_ids, start, end)
    seed_features_daily(player_ids, start, end)

    print("\n" + "=" * 60)
    print("Training ML models...")
    print("=" * 60)
    result = train_all()
    print(f"Training result: {result}")

    print("\n" + "=" * 60)
    print("Seed completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

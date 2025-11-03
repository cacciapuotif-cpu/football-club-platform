"""Seed script for 5 players (ages 15-19) with 5 sessions each."""
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import (
    Player, Session as TrainingSession,
    MetricsPhysical, MetricsTechnical, MetricsTactical, MetricsPsych,
    AnalyticsOutputs
)
from app.models.enums import (
    PlayerRole, DominantFoot, SessionType, PitchType,
    TimeOfDay, PlayerStatus
)


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created successfully")


def seed_database():
    """Seed database with 5 players (ages 15-19) and 5 sessions each."""
    db = SessionLocal()

    try:
        # Clear existing data
        print("\nClearing existing data...")
        db.query(AnalyticsOutputs).delete()
        db.query(MetricsPsych).delete()
        db.query(MetricsTactical).delete()
        db.query(MetricsTechnical).delete()
        db.query(MetricsPhysical).delete()
        db.query(TrainingSession).delete()
        db.query(Player).delete()
        db.commit()
        print("[OK] Existing data cleared")

        # Today's date
        today = date.today()

        # Define 5 players with different ages
        players_data = [
            {
                "age": 15,
                "code": "PLR015",
                "first_name": "Marco",
                "last_name": "Esposito",
                "birth_date": date(today.year - 15, 6, 20),
                "category": "U15",
                "primary_role": PlayerRole.MF,
                "secondary_role": PlayerRole.DF,
                "dominant_foot": DominantFoot.RIGHT,
                "shirt_number": 7,
                "years_active": 2
            },
            {
                "age": 16,
                "code": "PLR016",
                "first_name": "Luca",
                "last_name": "Bianchi",
                "birth_date": date(today.year - 16, 3, 15),
                "category": "U17",
                "primary_role": PlayerRole.MF,
                "secondary_role": PlayerRole.FW,
                "dominant_foot": DominantFoot.RIGHT,
                "shirt_number": 10,
                "years_active": 3
            },
            {
                "age": 17,
                "code": "PLR017",
                "first_name": "Matteo",
                "last_name": "Ferrari",
                "birth_date": date(today.year - 17, 9, 8),
                "category": "U17",
                "primary_role": PlayerRole.DF,
                "secondary_role": PlayerRole.MF,
                "dominant_foot": DominantFoot.LEFT,
                "shirt_number": 4,
                "years_active": 4
            },
            {
                "age": 18,
                "code": "PLR018",
                "first_name": "Alessandro",
                "last_name": "Rossi",
                "birth_date": date(today.year - 18, 1, 8),
                "category": "U19",
                "primary_role": PlayerRole.FW,
                "secondary_role": PlayerRole.MF,
                "dominant_foot": DominantFoot.LEFT,
                "shirt_number": 9,
                "years_active": 5
            },
            {
                "age": 19,
                "code": "PLR019",
                "first_name": "Giovanni",
                "last_name": "Romano",
                "birth_date": date(today.year - 19, 11, 25),
                "category": "U19",
                "primary_role": PlayerRole.GK,
                "secondary_role": None,
                "dominant_foot": DominantFoot.RIGHT,
                "shirt_number": 1,
                "years_active": 6
            }
        ]

        # Create players
        players = []
        print("\nCreating players...")
        for data in players_data:
            player = Player(
                code=data["code"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                date_of_birth=data["birth_date"],
                category=data["category"],
                primary_role=data["primary_role"],
                secondary_role=data["secondary_role"],
                dominant_foot=data["dominant_foot"],
                shirt_number=data["shirt_number"],
                years_active=data["years_active"]
            )
            db.add(player)
            db.flush()
            db.refresh(player)
            players.append((player, data["age"]))
            print(f"[OK] Created Player: {player.first_name} {player.last_name} ({data['age']} years old, {data['category']})")

        db.commit()
        print(f"\n[OK] Successfully created {len(players)} players")

        # Create 5 sessions for each player
        print("\nCreating training sessions...")

        for player, player_age in players:
            print(f"\n  Creating sessions for {player.first_name} {player.last_name}...")

            # Sessions over last 3 weeks
            for i in range(5):
                session_date = today - timedelta(days=21 - (i * 4))  # Every 4 days

                # Mix of training and matches
                is_match = i % 3 == 2  # Every 3rd session is a match
                session_type = SessionType.MATCH if is_match else SessionType.TRAINING

                # Base performance varies by age and improves over time
                age_factor = 1 + ((player_age - 15) * 0.05)  # +5% per year
                progression_factor = 1 + (i * 0.03)  # +3% per session

                # Create session
                session = TrainingSession(
                    player_id=player.id,
                    session_date=session_date,
                    session_type=session_type,
                    minutes_played=90 if is_match else random.randint(60, 90),
                    coach_rating=Decimal(str(round(5.5 + (i * 0.2) + random.uniform(-0.3, 0.5), 1))),
                    match_score=f"{random.randint(1,3)}-{random.randint(0,2)}" if is_match else None,
                    notes=f"{'Match day - good effort' if is_match else 'Training session - focus on technique'}",
                    pitch_type=PitchType.NATURAL if i % 2 == 0 else PitchType.SYNTHETIC,
                    weather=["Sunny", "Cloudy", "Rainy"][i % 3],
                    time_of_day=TimeOfDay.AFTERNOON if i % 2 == 0 else TimeOfDay.EVENING,
                    status=PlayerStatus.OK
                )
                db.add(session)
                db.flush()

                # Physical metrics (age-appropriate)
                base_height = 168 + (player_age - 15) * 2.5  # Height increases with age
                base_weight = 62 + (player_age - 15) * 2.0   # Weight increases with age

                # Goalkeeper has different physique
                if player.primary_role == PlayerRole.GK:
                    base_height += 8
                    base_weight += 6

                metrics_phys = MetricsPhysical(
                    session_id=session.id,
                    height_cm=Decimal(str(round(base_height + random.uniform(-1, 1), 2))),
                    weight_kg=Decimal(str(round(base_weight + random.uniform(-0.5, 0.5), 2))),
                    bmi=Decimal(str(round(base_weight / ((base_height/100) ** 2), 2))),
                    body_fat_pct=Decimal(str(round(11 + random.uniform(-1, 1), 2))),
                    lean_mass_kg=Decimal(str(round(base_weight * 0.89, 2))),
                    resting_hr_bpm=int(60 - player_age + random.randint(-3, 3)),
                    max_speed_kmh=Decimal(str(round((26 + age_factor * 2) * progression_factor, 2))),
                    accel_0_10m_s=Decimal(str(round(1.9 - (age_factor * 0.1) - (i * 0.01), 2))),
                    accel_0_20m_s=Decimal(str(round(3.3 - (age_factor * 0.15) - (i * 0.015), 2))),
                    distance_km=Decimal(str(round((8.0 + random.uniform(0, 1.5)) if is_match else (5.5 + random.uniform(0, 1)), 2))),
                    sprints_over_25kmh=int((12 + i + int(age_factor * 2)) if is_match else 6 + random.randint(0, 4)),
                    vertical_jump_cm=Decimal(str(round(42 + (age_factor * 2) + (i * 0.4), 2))),
                    agility_illinois_s=Decimal(str(round(17.0 - (age_factor * 0.2) - (i * 0.04), 2))),
                    yoyo_level=Decimal(str(round(16.5 + (age_factor * 0.5) + (i * 0.3), 2))),
                    rpe=Decimal(str(round(7.5 + random.uniform(-1, 0.5) if is_match else 6.0 + random.uniform(-0.5, 0.5), 1))),
                    sleep_hours=Decimal(str(round(8.0 + random.uniform(-0.5, 0.5), 2)))
                )
                db.add(metrics_phys)

                # Technical metrics (improving with age and practice)
                base_technical_skill = 65 + (player_age - 15) * 2  # Improves with age

                passes_attempted = int((35 + random.randint(0, 15)) * age_factor * progression_factor)
                passes_completed = int(passes_attempted * (0.75 + (age_factor * 0.03) + (i * 0.015)))

                shots_total = int((4 + random.randint(0, 3)) if is_match else 6 + random.randint(0, 3))
                shots_on_target = int(shots_total * (0.50 + (age_factor * 0.02) + (i * 0.03)))

                metrics_tech = MetricsTechnical(
                    session_id=session.id,
                    passes_attempted=passes_attempted,
                    passes_completed=passes_completed,
                    pass_accuracy_pct=Decimal(str(round((passes_completed / passes_attempted) * 100, 2))),
                    progressive_passes=int((6 + i + int(age_factor)) if is_match else 4 + random.randint(0, 2)),
                    long_pass_accuracy_pct=Decimal(str(round(55 + (age_factor * 2) + (i * 1.5), 2))),
                    shots=shots_total,
                    shots_on_target=shots_on_target,
                    shot_accuracy_pct=Decimal(str(round((shots_on_target / shots_total) * 100, 2))),
                    crosses=int(2 + random.randint(0, 2) if is_match else 1),
                    cross_accuracy_pct=Decimal(str(round(35 + (age_factor * 2) + (i * 2.5), 2))),
                    successful_dribbles=int((5 + i + int(age_factor)) if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else 2 + random.randint(0, 2)),
                    failed_dribbles=int(4 - (age_factor * 0.1) - (i * 0.15)),
                    dribble_success_pct=Decimal(str(round(55 + (age_factor * 2) + (i * 2), 2))),
                    ball_losses=int(9 - (age_factor * 0.2) - (i * 0.3)),
                    ball_recoveries=int(4 + (age_factor * 0.3) + (i * 0.5)),
                    set_piece_accuracy_pct=Decimal(str(round(45 + (age_factor * 2) + (i * 2.5), 2)))
                )
                db.add(metrics_tech)

                # Tactical metrics
                metrics_tact = MetricsTactical(
                    session_id=session.id,
                    xg=Decimal(str(round(0.25 + (age_factor * 0.05) + (i * 0.05) if is_match else 0.08, 3))),
                    xa=Decimal(str(round(0.15 + (age_factor * 0.03) + (i * 0.03) if is_match else 0.04, 3))),
                    pressures=int(18 + int(age_factor * 2) + (i * 2) if is_match else 12 + random.randint(0, 3)),
                    interceptions=int(3 + random.randint(0, 3) + int(age_factor * 0.5)),
                    heatmap_zone_json={"zones": ["midfield", "attacking_third"] if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else ["defensive_third", "midfield"]},
                    influence_zones_pct=Decimal(str(round(60 + (age_factor * 2) + (i * 1.5), 2))),
                    effective_off_ball_runs=int(7 + i + int(age_factor) if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else 3 + random.randint(0, 2)),
                    transition_reaction_time_s=Decimal(str(round(2.7 - (age_factor * 0.08) - (i * 0.05), 2))),
                    involvement_pct=Decimal(str(round(65 + (age_factor * 2) + (i * 1.5), 2)))
                )
                db.add(metrics_tact)

                # Psychological metrics (improving with experience and age)
                metrics_psych = MetricsPsych(
                    session_id=session.id,
                    attention_score=int(65 + int(age_factor * 3) + (i * 2)),
                    decision_making=int(5 + int(age_factor * 0.3) + (i * 0.25)),
                    motivation=int(7 + random.randint(-1, 1)),
                    stress_management=int(5 + int(age_factor * 0.25) + (i * 0.2)),
                    self_esteem=int(6 + int(age_factor * 0.2) + (i * 0.15)),
                    team_leadership=int(4 + int(age_factor * 0.3) + (i * 0.15)),
                    sleep_quality=int(7 + random.randint(-1, 1)),
                    mood_pre=int(7 + random.randint(-1, 1)),
                    mood_post=int(7 + random.randint(0, 2)),
                    tactical_adaptability=int(5 + int(age_factor * 0.3) + (i * 0.25))
                )
                db.add(metrics_psych)

                # Analytics outputs (calculated performance index)
                performance_index = Decimal(str(min(100.0, round(
                    (base_technical_skill + (i * 2)) * age_factor * progression_factor,
                    2
                ))))

                analytics = AnalyticsOutputs(
                    session_id=session.id,
                    performance_index=performance_index,
                    progress_index_rolling=Decimal(str(round(float(performance_index) * 0.97, 2))),
                    zscore_vs_player_baseline=Decimal(str(round(-0.6 + (i * 0.2) + (age_factor * 0.1), 3))),
                    cluster_label="TECH" if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else "PHYSICAL" if player.primary_role == PlayerRole.DF else "SPECIALIZED"
                )
                db.add(analytics)

                print(f"    [OK] Session {i+1}: {session_date} ({session_type.value})")

        db.commit()
        print(f"\n[OK] Successfully created 5 sessions for each player (25 total)")
        print("\n=== SEEDING COMPLETED SUCCESSFULLY ===")
        print(f"\nPlayers created:")
        for idx, (player, age) in enumerate(players, 1):
            print(f"  {idx}. {player.code} - {player.first_name} {player.last_name} ({age} years, {player.category})")
        print(f"\nTotal sessions created: 25 (5 per player)")
        print(f"\nYou can now access:")
        print(f"  - API: http://localhost:8000/docs")
        print(f"  - Frontend: http://localhost:3000/players")

    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=== FOOTBALL CLUB PLATFORM - DATABASE SEEDING ===")
    print("=== Creating 5 players (ages 15-19) with 5 sessions each ===\n")
    create_tables()
    seed_database()

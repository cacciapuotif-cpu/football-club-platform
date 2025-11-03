"""Seed script for 2 specific players (16 and 18 years old) with 10 sessions each."""
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
    """Seed database with 2 players (16 and 18 years old) and 10 sessions each."""
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
        today = date(2025, 10, 16)

        # Player 1: 16 years old (born March 15, 2009)
        player_16 = Player(
            code="PLR016",
            first_name="Luca",
            last_name="Bianchi",
            date_of_birth=date(2009, 3, 15),
            category="U17",
            primary_role=PlayerRole.MF,
            secondary_role=PlayerRole.FW,
            dominant_foot=DominantFoot.RIGHT,
            shirt_number=10,
            years_active=3
        )

        # Player 2: 18 years old (born January 8, 2007)
        player_18 = Player(
            code="PLR018",
            first_name="Alessandro",
            last_name="Rossi",
            date_of_birth=date(2007, 1, 8),
            category="U19",
            primary_role=PlayerRole.FW,
            secondary_role=PlayerRole.MF,
            dominant_foot=DominantFoot.LEFT,
            shirt_number=9,
            years_active=5
        )

        db.add(player_16)
        db.add(player_18)
        db.commit()
        db.refresh(player_16)
        db.refresh(player_18)

        print(f"\n[OK] Created Player 1: {player_16.first_name} {player_16.last_name} (16 years old)")
        print(f"[OK] Created Player 2: {player_18.first_name} {player_18.last_name} (18 years old)")

        # Create 10 sessions for each player
        print("\nCreating training sessions...")

        for player, player_age in [(player_16, 16), (player_18, 18)]:
            print(f"\n  Creating sessions for {player.first_name} {player.last_name}...")

            # Sessions over last 5 weeks (2 per week)
            for i in range(10):
                session_date = today - timedelta(days=35 - (i * 3))  # Every 3 days

                # Alternate between training and match
                is_match = i % 4 == 3  # Every 4th session is a match
                session_type = SessionType.MATCH if is_match else SessionType.TRAINING

                # Base performance improves slightly over time
                progression_factor = 1 + (i * 0.02)  # +2% per session

                # Create session
                session = TrainingSession(
                    player_id=player.id,
                    session_date=session_date,
                    session_type=session_type,
                    minutes_played=90 if is_match else random.randint(60, 90),
                    coach_rating=Decimal(str(round(6.0 + (i * 0.15) + random.uniform(-0.5, 0.5), 1))),
                    match_score="2-1" if is_match and i < 7 else "3-2" if is_match else None,
                    notes=f"{'Good match performance' if is_match else 'Solid training session'}",
                    pitch_type=PitchType.NATURAL,
                    weather="Sunny" if i % 3 == 0 else "Cloudy",
                    time_of_day=TimeOfDay.AFTERNOON if i % 2 == 0 else TimeOfDay.EVENING,
                    status=PlayerStatus.OK
                )
                db.add(session)
                db.flush()

                # Physical metrics (age-appropriate)
                base_height = 172 if player_age == 16 else 178
                base_weight = 65 if player_age == 16 else 72

                metrics_phys = MetricsPhysical(
                    session_id=session.id,
                    height_cm=Decimal(str(base_height + random.uniform(-1, 1))),
                    weight_kg=Decimal(str(base_weight + random.uniform(-0.5, 0.5))),
                    bmi=Decimal(str(round(base_weight / ((base_height/100) ** 2), 2))),
                    body_fat_pct=Decimal(str(round(10 + random.uniform(-1, 1), 2))),
                    lean_mass_kg=Decimal(str(round(base_weight * 0.9, 2))),
                    resting_hr_bpm=int(55 + random.randint(-5, 5)),
                    max_speed_kmh=Decimal(str(round((28 + (player_age - 16) * 0.5) * progression_factor, 2))),
                    accel_0_10m_s=Decimal(str(round(1.8 - (i * 0.01), 2))),
                    accel_0_20m_s=Decimal(str(round(3.1 - (i * 0.015), 2))),
                    distance_km=Decimal(str(round((8.5 + random.uniform(0, 2)) if is_match else (6.0 + random.uniform(0, 1.5)), 2))),
                    sprints_over_25kmh=int((15 + i) if is_match else 8 + random.randint(0, 5)),
                    vertical_jump_cm=Decimal(str(round(45 + (player_age - 16) + (i * 0.3), 2))),
                    agility_illinois_s=Decimal(str(round(16.5 - (i * 0.05), 2))),
                    yoyo_level=Decimal(str(round(18.0 + (i * 0.2), 2))),
                    rpe=Decimal(str(round(7.0 + random.uniform(-1, 1) if is_match else 5.5 + random.uniform(-0.5, 0.5), 1))),
                    sleep_hours=Decimal(str(round(7.5 + random.uniform(-0.5, 1), 2)))
                )
                db.add(metrics_phys)

                # Technical metrics (improving with age and practice)
                base_technical_skill = 70 if player_age == 16 else 75

                passes_attempted = int((40 + random.randint(0, 20)) * progression_factor)
                passes_completed = int(passes_attempted * (0.80 + (i * 0.01)))

                shots_total = int((5 + random.randint(0, 3)) if is_match else 8 + random.randint(0, 4))
                shots_on_target = int(shots_total * (0.55 + (i * 0.02)))

                metrics_tech = MetricsTechnical(
                    session_id=session.id,
                    passes_attempted=passes_attempted,
                    passes_completed=passes_completed,
                    pass_accuracy_pct=Decimal(str(round((passes_completed / passes_attempted) * 100, 2))),
                    progressive_passes=int((8 + i) if is_match else 5 + random.randint(0, 3)),
                    long_pass_accuracy_pct=Decimal(str(round(60 + (i * 1.5), 2))),
                    shots=shots_total,
                    shots_on_target=shots_on_target,
                    shot_accuracy_pct=Decimal(str(round((shots_on_target / shots_total) * 100, 2))),
                    crosses=int(3 + random.randint(0, 2) if is_match else 1),
                    cross_accuracy_pct=Decimal(str(round(40 + (i * 2), 2))),
                    successful_dribbles=int((6 + i) if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else 3 + random.randint(0, 2)),
                    failed_dribbles=int(3 - (i * 0.1)),
                    dribble_success_pct=Decimal(str(round(60 + (i * 2), 2))),
                    ball_losses=int(8 - (i * 0.3)),
                    ball_recoveries=int(5 + (i * 0.5)),
                    set_piece_accuracy_pct=Decimal(str(round(50 + (i * 2), 2)))
                )
                db.add(metrics_tech)

                # Tactical metrics
                metrics_tact = MetricsTactical(
                    session_id=session.id,
                    xg=Decimal(str(round(0.3 + (i * 0.05) if is_match else 0.1, 3))),
                    xa=Decimal(str(round(0.2 + (i * 0.03) if is_match else 0.05, 3))),
                    pressures=int(20 + (i * 2) if is_match else 15),
                    interceptions=int(4 + random.randint(0, 3)),
                    heatmap_zone_json={"zones": ["midfield", "attacking_third"]},
                    influence_zones_pct=Decimal(str(round(65 + (i * 1.5), 2))),
                    effective_off_ball_runs=int(8 + i if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else 4),
                    transition_reaction_time_s=Decimal(str(round(2.5 - (i * 0.05), 2))),
                    involvement_pct=Decimal(str(round(70 + (i * 1.5), 2)))
                )
                db.add(metrics_tact)

                # Psychological metrics (improving with experience)
                metrics_psych = MetricsPsych(
                    session_id=session.id,
                    attention_score=int(70 + (i * 2)),
                    decision_making=int(6 + (i * 0.2)),
                    motivation=int(7 + random.randint(0, 1)),
                    stress_management=int(6 + (i * 0.15)),
                    self_esteem=int(7 + (i * 0.1)),
                    team_leadership=int(5 + (player_age - 16) + (i * 0.1)),
                    sleep_quality=int(7 + random.randint(-1, 1)),
                    mood_pre=int(7 + random.randint(-1, 1)),
                    mood_post=int(7 + random.randint(0, 2)),
                    tactical_adaptability=int(6 + (i * 0.2))
                )
                db.add(metrics_psych)

                # Analytics outputs (calculated performance index)
                performance_index = Decimal(str(min(100.0, round(
                    (base_technical_skill + (i * 1.5)) * progression_factor,
                    2
                ))))

                analytics = AnalyticsOutputs(
                    session_id=session.id,
                    performance_index=performance_index,
                    progress_index_rolling=Decimal(str(round(float(performance_index) * 0.98, 2))),
                    zscore_vs_player_baseline=Decimal(str(round(-0.5 + (i * 0.15), 3))),
                    cluster_label="TECH" if player.primary_role in [PlayerRole.MF, PlayerRole.FW] else "PHYSICAL"
                )
                db.add(analytics)

                print(f"    [OK] Session {i+1}: {session_date} ({session_type.value})")

        db.commit()
        print(f"\n[OK] Successfully created 10 sessions for each player (20 total)")
        print("\n=== SEEDING COMPLETED SUCCESSFULLY ===")
        print(f"\nPlayers created:")
        print(f"  1. {player_16.code} - {player_16.first_name} {player_16.last_name} (16 years, {player_16.category})")
        print(f"  2. {player_18.code} - {player_18.first_name} {player_18.last_name} (18 years, {player_18.category})")
        print(f"\nTotal sessions created: 20 (10 per player)")
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
    print("=== FOOTBALL CLUB PLATFORM - DATABASE SEEDING ===\n")
    create_tables()
    seed_database()

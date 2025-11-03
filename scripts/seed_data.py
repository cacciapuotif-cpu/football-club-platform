"""Seed database with realistic player data."""
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import (
    Player, Session as SessionModel, MetricsPhysical,
    MetricsTechnical, MetricsTactical, MetricsPsych, AnalyticsOutputs
)
from app.models.enums import PlayerRole, DominantFoot, SessionType, PlayerStatus
from app.services.calculations import apply_all_calculations


def create_tables():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def seed_player(db: Session) -> Player:
    """Create a realistic 16-year-old midfielder."""
    print("\nCreating player...")

    player = Player(
        code="P-0017",
        first_name="Marco",
        last_name="Rossi",
        date_of_birth=date(2008, 3, 15),  # 16 years old
        category="U17",
        primary_role=PlayerRole.MF,
        secondary_role=None,
        dominant_foot=DominantFoot.RIGHT,
        shirt_number=8,
        years_active=2
    )

    db.add(player)
    db.commit()
    db.refresh(player)

    print(f"✓ Player created: {player.first_name} {player.last_name} (Code: {player.code})")
    return player


def seed_sessions(db: Session, player: Player, num_weeks: int = 24):
    """
    Create realistic sessions for 24 weeks with improvement trend.

    Pattern: 3-4 sessions per week (2-3 training + 1 match)
    """
    print(f"\nCreating {num_weeks} weeks of sessions...")

    start_date = date.today() - timedelta(weeks=num_weeks)
    session_count = 0

    # Base metrics (will improve over time)
    base_metrics = {
        'height_cm': Decimal('176.0'),
        'weight_kg': Decimal('66.5'),
        'body_fat_pct': Decimal('12.4'),
        'resting_hr_bpm': 58,
        'distance_km': Decimal('9.5'),
        'sprints_over_25kmh': 15,
        'yoyo_level': Decimal('21.0'),
        'passes_attempted': 55,
        'passes_completed': 45,
        'progressive_passes': 8,
        'successful_dribbles': 3,
        'interceptions': 5,
        'motivation': 7,
        'attention_score': 65
    }

    for week in range(num_weeks):
        week_date = start_date + timedelta(weeks=week)

        # Calculate improvement factor (gradual improvement over 24 weeks)
        improvement = week / num_weeks  # 0.0 to 1.0

        # Number of sessions this week (3 or 4)
        sessions_this_week = random.choice([3, 4])

        for session_num in range(sessions_this_week):
            session_date = week_date + timedelta(days=session_num * 2)

            # Last session of week is often a match
            is_match = (session_num == sessions_this_week - 1)
            session_type = SessionType.MATCH if is_match else SessionType.TRAINING

            # Apply improvement with some randomness
            def improve(base_value, max_improvement_pct=0.25):
                """Apply improvement with randomness."""
                if isinstance(base_value, (int, Decimal)):
                    variance = random.uniform(-0.05, 0.10)  # -5% to +10% daily variance
                    improved = float(base_value) * (1 + improvement * max_improvement_pct)
                    final = improved * (1 + variance)
                    return type(base_value)(round(final, 2 if isinstance(base_value, Decimal) else 0))
                return base_value

            # Create session
            session = SessionModel(
                player_id=player.id,
                session_date=session_date,
                session_type=session_type,
                minutes_played=90 if is_match else random.randint(60, 90),
                coach_rating=Decimal(str(round(random.uniform(6.5, 8.5), 1))),
                match_score="2-1" if is_match and random.random() > 0.5 else None,
                notes=f"{'Partita' if is_match else 'Allenamento'} settimana {week + 1}",
                status=PlayerStatus.OK
            )
            db.add(session)
            db.flush()

            # Physical metrics
            metrics_phys = MetricsPhysical(
                session_id=session.id,
                height_cm=base_metrics['height_cm'],
                weight_kg=improve(base_metrics['weight_kg'], -0.02),  # Slight weight optimization
                body_fat_pct=improve(base_metrics['body_fat_pct'], -0.15),  # Body fat reduction
                resting_hr_bpm=improve(base_metrics['resting_hr_bpm'], -0.10),  # Lower HR over time
                distance_km=improve(base_metrics['distance_km'], 0.20),  # +20% distance capacity
                sprints_over_25kmh=improve(base_metrics['sprints_over_25kmh'], 0.35),  # +35% sprint capacity
                yoyo_level=improve(base_metrics['yoyo_level'], 0.30),  # +30% endurance
                vertical_jump_cm=Decimal(str(random.uniform(38, 45))),
                rpe=Decimal(str(round(random.uniform(6.0, 8.5), 1))),
                sleep_hours=Decimal(str(round(random.uniform(7.0, 9.0), 1)))
            )
            db.add(metrics_phys)

            # Technical metrics
            passes_attempted = improve(base_metrics['passes_attempted'], 0.25)
            pass_completion_rate = 0.75 + (improvement * 0.15)  # 75% -> 90%
            passes_completed = int(passes_attempted * pass_completion_rate)

            metrics_tech = MetricsTechnical(
                session_id=session.id,
                passes_attempted=passes_attempted,
                passes_completed=passes_completed,
                progressive_passes=improve(base_metrics['progressive_passes'], 0.40),  # +40%
                shots=random.randint(1, 5) if is_match else random.randint(0, 3),
                shots_on_target=random.randint(0, 3) if is_match else random.randint(0, 2),
                successful_dribbles=improve(base_metrics['successful_dribbles'], 0.50),  # +50%
                failed_dribbles=random.randint(1, 3),
                ball_losses=random.randint(5, 12),
                ball_recoveries=improve(base_metrics['interceptions'], 0.30) + random.randint(3, 8),
                crosses=random.randint(0, 5) if is_match else 0,
                cross_accuracy_pct=Decimal(str(round(random.uniform(40, 70), 2)))
            )
            db.add(metrics_tech)

            # Tactical metrics
            metrics_tact = MetricsTactical(
                session_id=session.id,
                xg=Decimal(str(round(random.uniform(0.1, 0.8), 2))) if is_match else None,
                xa=Decimal(str(round(random.uniform(0.0, 0.5), 2))) if is_match else None,
                pressures=random.randint(15, 30),
                interceptions=improve(base_metrics['interceptions'], 0.35),  # +35%
                involvement_pct=Decimal(str(round(random.uniform(40, 65), 2))),
                effective_off_ball_runs=random.randint(5, 15)
            )
            db.add(metrics_tact)

            # Psychological metrics
            metrics_psych = MetricsPsych(
                session_id=session.id,
                attention_score=improve(base_metrics['attention_score'], 0.25),  # +25%
                motivation=improve(base_metrics['motivation'], 0.20),  # +20%
                stress_management=random.randint(6, 9),
                self_esteem=random.randint(7, 9),
                team_leadership=min(10, 5 + int(improvement * 4)),  # Gradual leadership growth
                sleep_quality=random.randint(6, 9),
                mood_pre=random.randint(6, 9),
                mood_post=random.randint(7, 10),
                decision_making=min(10, 6 + int(improvement * 3)),
                tactical_adaptability=min(10, 6 + int(improvement * 3))
            )
            db.add(metrics_psych)

            db.flush()

            # Calculate and save analytics
            calculations = apply_all_calculations(
                db=db,
                session_id=str(session.id),
                player_id=str(player.id),
                metrics_physical=metrics_phys,
                metrics_technical=metrics_tech
            )

            # Update calculated fields
            metrics_phys.bmi = calculations["bmi"]
            metrics_tech.pass_accuracy_pct = calculations["pass_accuracy_pct"]
            metrics_tech.shot_accuracy_pct = calculations["shot_accuracy_pct"]
            metrics_tech.dribble_success_pct = calculations["dribble_success_pct"]

            # Create analytics
            analytics = AnalyticsOutputs(
                session_id=session.id,
                performance_index=calculations["performance_index"],
                progress_index_rolling=calculations["progress_index_rolling"],
                zscore_vs_player_baseline=calculations["zscore_vs_player_baseline"],
                cluster_label=calculations["cluster_label"]
            )
            db.add(analytics)

            session_count += 1

            if session_count % 10 == 0:
                print(f"  Created {session_count} sessions...")

    db.commit()
    print(f"✓ Created {session_count} sessions with realistic improvement trend")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Football Club Platform - Database Seeding")
    print("=" * 60)

    # Create tables
    create_tables()

    # Get database session
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_player = db.query(Player).filter(Player.code == "P-0017").first()
        if existing_player:
            print("\n⚠️  Player P-0017 already exists!")
            response = input("Do you want to delete and recreate? (yes/no): ")
            if response.lower() != 'yes':
                print("Seeding cancelled.")
                return

            # Delete existing player (cascades to sessions)
            db.delete(existing_player)
            db.commit()
            print("✓ Existing data deleted")

        # Create seed data
        player = seed_player(db)
        seed_sessions(db, player, num_weeks=24)

        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print(f"\nCreated player: {player.code} - {player.first_name} {player.last_name}")
        print(f"Total sessions: ~{24 * 3.5:.0f} (24 weeks × ~3.5 sessions/week)")
        print("\nYou can now:")
        print("  - View the player in the UI")
        print("  - See the performance trend analytics")
        print("  - Export the data to CSV")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

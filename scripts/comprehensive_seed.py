"""
Comprehensive database seeding script with realistic football data.

This script populates the database with:
- 15 players with varied characteristics
- 300+ training sessions with realistic metrics
- Progressive performance trends
- Variety in session types (training, matches, tests)
"""

import random
from datetime import date, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.models import (
    Player, Session, MetricsPhysical, MetricsTechnical,
    MetricsTactical, MetricsPsych, AnalyticsOutputs
)
from app.models.enums import (
    PlayerRole, DominantFoot, SessionType, PitchType,
    TimeOfDay, PlayerStatus
)
from app.services.calculations import apply_all_calculations


# Player templates with realistic characteristics
PLAYER_TEMPLATES = [
    {
        "code": "PLR001",
        "first_name": "Marco",
        "last_name": "Rossi",
        "date_of_birth": date(2006, 3, 15),
        "category": "U19",
        "primary_role": PlayerRole.GK,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 1,
        "years_active": 3,
        "base_stats": {"physical": 75, "technical": 70, "tactical": 72, "psychological": 80}
    },
    {
        "code": "PLR002",
        "first_name": "Luca",
        "last_name": "Bianchi",
        "date_of_birth": date(2007, 7, 22),
        "category": "U18",
        "primary_role": PlayerRole.DF,
        "secondary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.LEFT,
        "shirt_number": 3,
        "years_active": 2,
        "base_stats": {"physical": 78, "technical": 74, "tactical": 80, "psychological": 75}
    },
    {
        "code": "PLR003",
        "first_name": "Alessandro",
        "last_name": "Conti",
        "date_of_birth": date(2006, 11, 5),
        "category": "U19",
        "primary_role": PlayerRole.DF,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 4,
        "years_active": 4,
        "base_stats": {"physical": 82, "technical": 70, "tactical": 85, "psychological": 78}
    },
    {
        "code": "PLR004",
        "first_name": "Matteo",
        "last_name": "Ferrari",
        "date_of_birth": date(2007, 2, 18),
        "category": "U18",
        "primary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.BOTH,
        "shirt_number": 8,
        "years_active": 2,
        "base_stats": {"physical": 76, "technical": 85, "tactical": 82, "psychological": 80}
    },
    {
        "code": "PLR005",
        "first_name": "Davide",
        "last_name": "Marino",
        "date_of_birth": date(2006, 9, 30),
        "category": "U19",
        "primary_role": PlayerRole.MF,
        "secondary_role": PlayerRole.FW,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 10,
        "years_active": 3,
        "base_stats": {"physical": 80, "technical": 88, "tactical": 86, "psychological": 85}
    },
    {
        "code": "PLR006",
        "first_name": "Lorenzo",
        "last_name": "Romano",
        "date_of_birth": date(2007, 5, 12),
        "category": "U18",
        "primary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.LEFT,
        "shirt_number": 7,
        "years_active": 2,
        "base_stats": {"physical": 74, "technical": 82, "tactical": 78, "psychological": 76}
    },
    {
        "code": "PLR007",
        "first_name": "Giovanni",
        "last_name": "Colombo",
        "date_of_birth": date(2006, 12, 8),
        "category": "U19",
        "primary_role": PlayerRole.FW,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 9,
        "years_active": 4,
        "base_stats": {"physical": 85, "technical": 80, "tactical": 75, "psychological": 82}
    },
    {
        "code": "PLR008",
        "first_name": "Francesco",
        "last_name": "Ricci",
        "date_of_birth": date(2007, 4, 25),
        "category": "U18",
        "primary_role": PlayerRole.FW,
        "secondary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.LEFT,
        "shirt_number": 11,
        "years_active": 2,
        "base_stats": {"physical": 79, "technical": 84, "tactical": 77, "psychological": 79}
    },
    {
        "code": "PLR009",
        "first_name": "Andrea",
        "last_name": "Greco",
        "date_of_birth": date(2006, 6, 14),
        "category": "U19",
        "primary_role": PlayerRole.DF,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 5,
        "years_active": 3,
        "base_stats": {"physical": 80, "technical": 72, "tactical": 83, "psychological": 77}
    },
    {
        "code": "PLR010",
        "first_name": "Simone",
        "last_name": "Leone",
        "date_of_birth": date(2007, 10, 3),
        "category": "U18",
        "primary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 6,
        "years_active": 2,
        "base_stats": {"physical": 77, "technical": 79, "tactical": 81, "psychological": 78}
    },
    {
        "code": "PLR011",
        "first_name": "Riccardo",
        "last_name": "De Luca",
        "date_of_birth": date(2006, 1, 20),
        "category": "U19",
        "primary_role": PlayerRole.FW,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 19,
        "years_active": 4,
        "base_stats": {"physical": 83, "technical": 82, "tactical": 76, "psychological": 84}
    },
    {
        "code": "PLR012",
        "first_name": "Tommaso",
        "last_name": "Santoro",
        "date_of_birth": date(2007, 8, 16),
        "category": "U18",
        "primary_role": PlayerRole.DF,
        "secondary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.LEFT,
        "shirt_number": 2,
        "years_active": 2,
        "base_stats": {"physical": 76, "technical": 75, "tactical": 79, "psychological": 74}
    },
    {
        "code": "PLR013",
        "first_name": "Gabriele",
        "last_name": "Marchetti",
        "date_of_birth": date(2006, 4, 9),
        "category": "U19",
        "primary_role": PlayerRole.MF,
        "dominant_foot": DominantFoot.BOTH,
        "shirt_number": 14,
        "years_active": 3,
        "base_stats": {"physical": 78, "technical": 86, "tactical": 84, "psychological": 81}
    },
    {
        "code": "PLR014",
        "first_name": "Nicola",
        "last_name": "Vitale",
        "date_of_birth": date(2007, 11, 28),
        "category": "U18",
        "primary_role": PlayerRole.FW,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 17,
        "years_active": 1,
        "base_stats": {"physical": 75, "technical": 78, "tactical": 73, "psychological": 76}
    },
    {
        "code": "PLR015",
        "first_name": "Emanuele",
        "last_name": "Moretti",
        "date_of_birth": date(2006, 10, 11),
        "category": "U19",
        "primary_role": PlayerRole.GK,
        "dominant_foot": DominantFoot.RIGHT,
        "shirt_number": 12,
        "years_active": 3,
        "base_stats": {"physical": 77, "technical": 72, "tactical": 74, "psychological": 82}
    },
]


def generate_realistic_physical_metrics(base_physical: int, session_type: str, date_index: int) -> dict:
    """Generate realistic physical metrics with progression over time."""
    # Add progression factor (players improve over time)
    progression = (date_index / 365) * 5  # +5 points over a year
    adjusted_base = base_physical + progression + random.uniform(-3, 3)

    # Session type influences intensity
    intensity_factor = {
        SessionType.TRAINING: 0.8,
        SessionType.MATCH: 1.2,
        SessionType.TEST: 0.6
    }.get(session_type, 0.8)

    return {
        "height_cm": random.uniform(170, 185),
        "weight_kg": random.uniform(65, 80),
        "body_fat_pct": random.uniform(8, 14),
        "lean_mass_kg": random.uniform(55, 70),
        "resting_hr_bpm": random.randint(45, 65),
        "max_speed_kmh": (adjusted_base / 100) * random.uniform(30, 36) * intensity_factor,
        "accel_0_10m_s": random.uniform(1.65, 1.95),
        "accel_0_20m_s": random.uniform(2.85, 3.25),
        "distance_km": (adjusted_base / 100) * random.uniform(4, 10) * intensity_factor,
        "sprints_over_25kmh": int((adjusted_base / 100) * random.randint(5, 25) * intensity_factor),
        "vertical_jump_cm": random.uniform(40, 60),
        "agility_illinois_s": random.uniform(14, 17),
        "yoyo_level": random.uniform(16, 21),
        "rpe": min(10, max(1, (intensity_factor * 5) + random.uniform(-1, 2))),
        "sleep_hours": random.uniform(6.5, 9)
    }


def generate_realistic_technical_metrics(base_technical: int, role: str, session_type: str, date_index: int) -> dict:
    """Generate realistic technical metrics based on player role."""
    progression = (date_index / 365) * 5
    adjusted_base = base_technical + progression + random.uniform(-2, 2)

    # Role-based statistics
    role_factors = {
        PlayerRole.GK: {"passes": 0.3, "shots": 0.1, "dribbles": 0.1},
        PlayerRole.DF: {"passes": 0.9, "shots": 0.2, "dribbles": 0.4},
        PlayerRole.MF: {"passes": 1.2, "shots": 0.6, "dribbles": 0.8},
        PlayerRole.FW: {"passes": 0.7, "shots": 1.3, "dribbles": 1.0}
    }
    factors = role_factors.get(role, {"passes": 1.0, "shots": 0.5, "dribbles": 0.7})

    intensity = 1.5 if session_type == SessionType.MATCH else 1.0

    passes_attempted = int((adjusted_base / 100) * random.randint(20, 80) * factors["passes"] * intensity)
    passes_completed = int(passes_attempted * random.uniform(0.7, 0.95))

    shots = int((adjusted_base / 100) * random.randint(0, 10) * factors["shots"] * intensity)
    shots_on_target = int(shots * random.uniform(0.3, 0.7))

    return {
        "passes_attempted": passes_attempted,
        "passes_completed": passes_completed,
        "progressive_passes": int(passes_completed * random.uniform(0.1, 0.3)),
        "long_pass_accuracy_pct": random.uniform(60, 85),
        "shots": shots,
        "shots_on_target": shots_on_target,
        "crosses": int(factors["passes"] * random.randint(0, 8) * intensity),
        "cross_accuracy_pct": random.uniform(25, 55),
        "successful_dribbles": int((adjusted_base / 100) * random.randint(0, 12) * factors["dribbles"] * intensity),
        "failed_dribbles": int(random.randint(0, 8) * factors["dribbles"] * intensity),
        "ball_losses": int(random.randint(2, 15) * intensity),
        "ball_recoveries": int(random.randint(3, 18) * intensity),
        "set_piece_accuracy_pct": random.uniform(40, 75)
    }


def generate_realistic_tactical_metrics(base_tactical: int, role: str, session_type: str) -> dict:
    """Generate realistic tactical metrics."""
    intensity = 1.5 if session_type == SessionType.MATCH else 1.0

    role_factors = {
        PlayerRole.GK: {"def": 0.1, "off": 0.1},
        PlayerRole.DF: {"def": 1.3, "off": 0.4},
        PlayerRole.MF: {"def": 0.8, "off": 0.9},
        PlayerRole.FW: {"def": 0.3, "off": 1.4}
    }
    factors = role_factors.get(role, {"def": 1.0, "off": 1.0})

    return {
        "xg": random.uniform(0, 1.5) * factors["off"] * intensity,
        "xa": random.uniform(0, 1.2) * factors["off"] * intensity,
        "pressures": int((base_tactical / 100) * random.randint(5, 35) * factors["def"] * intensity),
        "interceptions": int((base_tactical / 100) * random.randint(0, 12) * factors["def"] * intensity),
        "heatmap_zone_json": None,
        "influence_zones_pct": random.uniform(50, 85),
        "effective_off_ball_runs": int(random.randint(3, 20) * factors["off"] * intensity),
        "transition_reaction_time_s": random.uniform(1.8, 3.5),
        "involvement_pct": random.uniform(60, 90)
    }


def generate_realistic_psych_metrics(base_psych: int, date_index: int) -> dict:
    """Generate realistic psychological metrics with seasonal variation."""
    # Seasonal fatigue (increases fatigue in mid-season)
    season_factor = abs((date_index % 180) - 90) / 90  # 0-1-0 cycle

    progression = (date_index / 365) * 2
    adjusted_base = min(10, (base_psych / 10) + (progression / 10))

    return {
        "attention_score": int(min(100, (adjusted_base * 10) + random.randint(-10, 10))),
        "decision_making": int(min(10, max(1, adjusted_base + random.uniform(-0.5, 0.5)))),
        "motivation": int(min(10, max(1, adjusted_base + random.uniform(-1, 1) * season_factor))),
        "stress_management": int(min(10, max(1, adjusted_base - (season_factor * 2) + random.uniform(-0.5, 0.5)))),
        "self_esteem": int(min(10, max(1, adjusted_base + random.uniform(-0.5, 0.5)))),
        "team_leadership": int(min(10, max(1, adjusted_base + random.uniform(-1, 1)))),
        "sleep_quality": int(min(10, max(1, (adjusted_base * 0.9) + random.uniform(-1, 1)))),
        "mood_pre": int(min(10, max(1, adjusted_base + random.uniform(-1, 1)))),
        "mood_post": int(min(10, max(1, adjusted_base + random.uniform(-0.5, 1.5)))),
        "tactical_adaptability": int(min(10, max(1, adjusted_base + random.uniform(-0.5, 0.5))))
    }


def seed_database():
    """Main seeding function."""
    print("Starting comprehensive database seeding...")
    db = SessionLocal()

    try:
        # Create players
        players = []
        for template in PLAYER_TEMPLATES:
            base_stats = template.pop("base_stats")
            player = Player(**template)
            db.add(player)
            players.append((player, base_stats))
            print(f"Created player: {player.first_name} {player.last_name} ({player.primary_role})")

        db.commit()
        print(f"\nCreated {len(players)} players")

        # Generate sessions for each player
        total_sessions = 0
        start_date = date.today() - timedelta(days=365)  # One year of data

        for player, base_stats in players:
            print(f"\nGenerating sessions for {player.first_name} {player.last_name}...")
            sessions_count = random.randint(18, 25)  # 18-25 sessions per player

            for i in range(sessions_count):
                # Generate session date (distributed over the year)
                days_offset = int((365 / sessions_count) * i) + random.randint(-3, 3)
                session_date = start_date + timedelta(days=days_offset)

                # Determine session type (80% training, 15% match, 5% test)
                rand = random.random()
                if rand < 0.80:
                    session_type = SessionType.TRAINING
                elif rand < 0.95:
                    session_type = SessionType.MATCH
                else:
                    session_type = SessionType.TEST

                # Create session
                session = Session(
                    player_id=player.id,
                    session_date=session_date,
                    session_type=session_type,
                    minutes_played=random.randint(60, 90) if session_type != SessionType.TEST else random.randint(30, 60),
                    coach_rating=Decimal(str(round(random.uniform(5.5, 9.0), 1))),
                    match_score=f"{random.randint(0, 4)}-{random.randint(0, 4)}" if session_type == SessionType.MATCH else None,
                    notes=f"Sessione {session_type.value.lower()} - Giorno {i+1}",
                    video_url=None,
                    pitch_type=random.choice([PitchType.NATURAL, PitchType.SYNTHETIC]),
                    weather=random.choice(["Sereno, 20°C", "Nuvoloso, 15°C", "Piovoso, 12°C", "Soleggiato, 25°C"]),
                    time_of_day=random.choice([TimeOfDay.MORNING, TimeOfDay.AFTERNOON, TimeOfDay.EVENING]),
                    status=PlayerStatus.OK
                )
                db.add(session)
                db.flush()

                # Generate metrics
                phys_metrics = generate_realistic_physical_metrics(
                    base_stats["physical"], session_type, i
                )
                tech_metrics = generate_realistic_technical_metrics(
                    base_stats["technical"], player.primary_role, session_type, i
                )
                tact_metrics = generate_realistic_tactical_metrics(
                    base_stats["tactical"], player.primary_role, session_type
                )
                psych_metrics = generate_realistic_psych_metrics(
                    base_stats["psychological"], i
                )

                # Create metrics
                metrics_phys = MetricsPhysical(
                    session_id=session.id,
                    **{k: Decimal(str(round(v, 2))) if isinstance(v, float) else v
                       for k, v in phys_metrics.items()}
                )
                metrics_tech = MetricsTechnical(
                    session_id=session.id,
                    **{k: Decimal(str(round(v, 2))) if isinstance(v, float) else v
                       for k, v in tech_metrics.items()}
                )
                metrics_tact = MetricsTactical(
                    session_id=session.id,
                    **{k: Decimal(str(round(v, 2))) if isinstance(v, float) and k != 'heatmap_zone_json' else v
                       for k, v in tact_metrics.items()}
                )
                metrics_psych = MetricsPsych(
                    session_id=session.id,
                    **psych_metrics
                )

                db.add_all([metrics_phys, metrics_tech, metrics_tact, metrics_psych])
                db.flush()

                # Calculate analytics
                calculations = apply_all_calculations(
                    db=db,
                    session_id=str(session.id),
                    player_id=str(player.id),
                    metrics_physical=metrics_phys,
                    metrics_technical=metrics_tech
                )

                # Update calculated metrics
                metrics_phys.bmi = calculations["bmi"]
                metrics_tech.pass_accuracy_pct = calculations["pass_accuracy_pct"]
                metrics_tech.shot_accuracy_pct = calculations["shot_accuracy_pct"]
                metrics_tech.dribble_success_pct = calculations["dribble_success_pct"]

                # Create analytics output
                analytics = AnalyticsOutputs(
                    session_id=session.id,
                    performance_index=calculations["performance_index"],
                    progress_index_rolling=calculations["progress_index_rolling"],
                    zscore_vs_player_baseline=calculations["zscore_vs_player_baseline"],
                    cluster_label=calculations["cluster_label"]
                )
                db.add(analytics)

                total_sessions += 1

                if (i + 1) % 5 == 0:
                    print(f"  Generated {i + 1}/{sessions_count} sessions")

        db.commit()
        print(f"\n✓ Successfully created {total_sessions} sessions with complete metrics!")
        print(f"✓ Database seeding completed!")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

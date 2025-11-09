"""Seed script for PlayerStats demo data."""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from app.models.player import Player, PlayerRole
from app.models.player_stats import PlayerStats
from app.models.match import Match
from app.services.advanced_ml_algorithms import advanced_ml


async def seed_player_stats():
    """Seed demo PlayerStats data for testing."""
    print("🌱 Seeding PlayerStats demo data...")

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch all players
        players_stmt = select(Player).where(Player.is_active == True).limit(20)
        result = await session.execute(players_stmt)
        players = result.scalars().all()

        if not players:
            print("❌ No players found. Please seed players first.")
            return

        print(f"✅ Found {len(players)} players")

        # Fetch recent matches
        matches_stmt = select(Match).order_by(Match.date.desc()).limit(10)
        matches_result = await session.execute(matches_stmt)
        matches = matches_result.scalars().all()

        print(f"✅ Found {len(matches)} matches")

        # Generate stats for each player
        stats_count = 0
        current_date = datetime.now().date()
        season = "2024-2025"

        for player in players:
            # Generate 5-10 match stats per player
            num_matches = random.randint(5, 10)

            for i in range(num_matches):
                match_date = current_date - timedelta(days=i * 7)  # Weekly matches
                match_id = matches[i % len(matches)].id if matches else None

                # Generate position-specific stats
                stats = _generate_stats_for_position(player.role_primary, player.id)
                stats.match_id = match_id
                stats.date = match_date
                stats.season = season
                stats.organization_id = player.organization_id

                # Calculate efficiency metrics
                stats.calculate_efficiency_metrics()

                # Calculate ML metrics
                stats.performance_index = advanced_ml.calculate_performance_index(
                    stats, player.role_primary
                )
                stats.influence_score = advanced_ml.calculate_influence_score(stats)
                stats.expected_goals_xg = advanced_ml.calculate_expected_goals(
                    stats, player.role_primary
                )
                stats.expected_assists_xa = advanced_ml.calculate_expected_assists(stats)

                session.add(stats)
                stats_count += 1

            # Update player ratings based on stats
            form = await advanced_ml.predict_player_form(session, str(player.id))
            player.form_level = form
            player.overall_rating = min(10, max(5, form + random.uniform(-1, 1)))
            player.potential_rating = min(10, player.overall_rating + random.uniform(0, 1.5))
            player.market_value_eur = _calculate_market_value(
                player.overall_rating,
                (datetime.now().date() - player.date_of_birth).days // 365
            )

        await session.commit()
        print(f"✅ Created {stats_count} player stats entries")
        print("✅ Updated player ratings and market values")
        print("🎉 PlayerStats seeding complete!")

    await engine.dispose()


def _generate_stats_for_position(position: str, player_id) -> PlayerStats:
    """Generate realistic stats based on player position."""
    stats = PlayerStats(
        id=uuid4(),
        player_id=player_id,
        minutes_played=random.randint(60, 90),
        is_starter=random.random() > 0.3
    )

    if position == PlayerRole.GK:
        # Goalkeeper stats
        stats.saves = random.randint(3, 12)
        stats.saves_from_inside_box = random.randint(1, 5)
        stats.punches = random.randint(0, 3)
        stats.high_claims = random.randint(2, 8)
        stats.catches = random.randint(3, 10)
        stats.sweeper_clearances = random.randint(0, 4)
        stats.goal_kicks = random.randint(10, 25)
        stats.passes_attempted = random.randint(20, 40)
        stats.passes_completed = random.randint(15, 35)
        stats.clearances = random.randint(2, 8)

    elif position == PlayerRole.DF:
        # Defender stats
        stats.tackles_attempted = random.randint(3, 10)
        stats.tackles_success = random.randint(2, 8)
        stats.interceptions = random.randint(2, 8)
        stats.clearances = random.randint(4, 12)
        stats.blocks = random.randint(1, 4)
        stats.aerial_duels_won = random.randint(2, 8)
        stats.aerial_duels_lost = random.randint(1, 4)
        stats.passes_attempted = random.randint(30, 60)
        stats.passes_completed = random.randint(25, 55)
        stats.long_balls = random.randint(5, 15)
        stats.long_balls_completed = random.randint(3, 10)
        stats.shots = random.randint(0, 2)
        stats.shots_on_target = random.randint(0, 1)
        stats.goals = 1 if random.random() > 0.9 else 0
        stats.assists = 1 if random.random() > 0.85 else 0

    elif position == PlayerRole.MF:
        # Midfielder stats
        stats.passes_attempted = random.randint(40, 80)
        stats.passes_completed = random.randint(32, 70)
        stats.key_passes = random.randint(1, 6)
        stats.through_balls = random.randint(0, 3)
        stats.crosses = random.randint(2, 8)
        stats.cross_accuracy_pct = random.uniform(20, 50)
        stats.dribbles_attempted = random.randint(3, 10)
        stats.dribbles_success = random.randint(2, 7)
        stats.tackles_attempted = random.randint(2, 6)
        stats.tackles_success = random.randint(1, 5)
        stats.interceptions = random.randint(1, 5)
        stats.shots = random.randint(1, 5)
        stats.shots_on_target = random.randint(0, 3)
        stats.goals = 1 if random.random() > 0.7 else 0
        stats.assists = random.randint(0, 2)
        stats.duels_won = random.randint(3, 10)
        stats.duels_lost = random.randint(2, 6)

    elif position == PlayerRole.FW:
        # Forward stats
        stats.shots = random.randint(3, 10)
        stats.shots_on_target = random.randint(1, 6)
        stats.goals = random.randint(0, 3)
        stats.assists = random.randint(0, 2)
        stats.dribbles_attempted = random.randint(4, 12)
        stats.dribbles_success = random.randint(2, 8)
        stats.key_passes = random.randint(1, 4)
        stats.through_balls = random.randint(0, 2)
        stats.passes_attempted = random.randint(20, 40)
        stats.passes_completed = random.randint(15, 35)
        stats.aerial_duels_won = random.randint(2, 8)
        stats.aerial_duels_lost = random.randint(1, 5)
        stats.offsides = random.randint(0, 3)
        stats.fouls_suffered = random.randint(1, 4)

    # Common stats for all positions
    stats.distance_covered_m = random.randint(8000, 12000)
    stats.sprints = random.randint(10, 30)
    stats.top_speed_kmh = random.uniform(28, 35)
    stats.fouls_committed = random.randint(0, 3)
    stats.yellow_cards = 1 if random.random() > 0.85 else 0
    stats.red_cards = 1 if random.random() > 0.98 else 0

    return stats


def _calculate_market_value(rating: float, age: int) -> float:
    """Calculate estimated market value based on rating and age."""
    base_value = 100000  # 100k EUR base

    # Rating multiplier (exponential)
    rating_multiplier = (rating / 6.0) ** 2.5

    # Age multiplier (peak at 24-27)
    if age < 24:
        age_multiplier = 0.7 + (age - 18) * 0.05
    elif age <= 27:
        age_multiplier = 1.0
    else:
        age_multiplier = max(0.3, 1.0 - (age - 27) * 0.1)

    market_value = base_value * rating_multiplier * age_multiplier * random.uniform(0.8, 1.2)
    return round(market_value, 2)


if __name__ == "__main__":
    asyncio.run(seed_player_stats())

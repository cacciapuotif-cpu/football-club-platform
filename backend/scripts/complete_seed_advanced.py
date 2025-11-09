"""Complete seed script with advanced analytics data."""

import asyncio
import random
from datetime import datetime, timedelta, date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from app.models.organization import Organization
from app.models.team import Team, Season
from app.models.player import Player, PlayerRole, DominantFoot
from app.models.match import Match
from app.models.player_stats import PlayerStats
from app.models.user import User
from app.services.advanced_ml_algorithms import advanced_ml


async def create_organization(session: AsyncSession) -> Organization:
    """Create demo organization."""
    org = Organization(
        id=uuid4(),
        name="Demo Football Club",
        country="IT",
        timezone="Europe/Rome",
        is_active=True
    )
    session.add(org)
    await session.commit()
    await session.refresh(org)
    print(f"✅ Organization created: {org.name}")
    return org


async def create_admin_user(session: AsyncSession, org_id) -> User:
    """Create admin user."""
    from app.services.security import get_password_hash

    user = User(
        id=uuid4(),
        email="admin@demo.club",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin Demo",
        role="ADMIN",
        organization_id=org_id,
        is_active=True,
        email_verified=True
    )
    session.add(user)
    await session.commit()
    print(f"✅ Admin user created: {user.email} / admin123")
    return user


async def create_teams(session: AsyncSession, org_id) -> list[Team]:
    """Create sample teams."""
    teams_data = [
        {"name": "AC Milan", "short_name": "MIL", "city": "Milano"},
        {"name": "Inter Milano", "short_name": "INT", "city": "Milano"},
        {"name": "Juventus", "short_name": "JUV", "city": "Torino"},
        {"name": "AS Roma", "short_name": "ROM", "city": "Roma"},
        {"name": "SSC Napoli", "short_name": "NAP", "city": "Napoli"},
        {"name": "SS Lazio", "short_name": "LAZ", "city": "Roma"},
        {"name": "Atalanta BC", "short_name": "ATA", "city": "Bergamo"},
        {"name": "Fiorentina", "short_name": "FIO", "city": "Firenze"}
    ]

    teams = []
    for team_data in teams_data:
        team = Team(
            id=uuid4(),
            organization_id=org_id,
            name=team_data["name"],
            short_name=team_data["short_name"],
            city=team_data["city"],
            is_active=True
        )
        teams.append(team)
        session.add(team)

    await session.commit()
    print(f"✅ Created {len(teams)} teams")
    return teams


async def create_season(session: AsyncSession, org_id) -> Season:
    """Create current season."""
    season = Season(
        id=uuid4(),
        organization_id=org_id,
        name="2024-2025",
        start_date=date(2024, 8, 1),
        end_date=date(2025, 5, 31),
        is_active=True
    )
    session.add(season)
    await session.commit()
    print(f"✅ Season created: {season.name}")
    return season


async def create_players(session: AsyncSession, org_id, teams: list[Team]) -> list[Player]:
    """Create realistic players for all teams."""
    first_names = [
        "Marco", "Luca", "Alessandro", "Matteo", "Lorenzo", "Andrea", "Davide",
        "Francesco", "Giovanni", "Simone", "Paolo", "Roberto", "Antonio", "Giuseppe",
        "Carlos", "João", "Pierre", "Thomas", "James", "Kevin", "Mohamed"
    ]
    last_names = [
        "Rossi", "Bianchi", "Verdi", "Ferrari", "Romano", "Colombo", "Ricci",
        "Silva", "Santos", "Costa", "Müller", "Schmidt", "Dubois", "Martin",
        "Smith", "Johnson", "Brown", "Garcia", "Rodriguez", "Martinez"
    ]

    players = []
    player_count_by_position = {
        PlayerRole.GK: 2,
        PlayerRole.DF: 8,
        PlayerRole.MF: 8,
        PlayerRole.FW: 4
    }

    for team in teams:
        jersey_nums = list(range(1, 100))
        random.shuffle(jersey_nums)
        jersey_idx = 0

        for role, count in player_count_by_position.items():
            for i in range(count):
                age = random.randint(18, 35)
                birth_year = datetime.now().year - age

                player = Player(
                    id=uuid4(),
                    organization_id=org_id,
                    team_id=team.id,
                    first_name=random.choice(first_names),
                    last_name=random.choice(last_names),
                    date_of_birth=date(birth_year, random.randint(1, 12), random.randint(1, 28)),
                    nationality="IT",
                    role_primary=role,
                    role_secondary=random.choice([None, role]),
                    dominant_foot=random.choice([DominantFoot.LEFT, DominantFoot.RIGHT]),
                    jersey_number=jersey_nums[jersey_idx],
                    height_cm=random.uniform(165, 195),
                    weight_kg=random.uniform(65, 95),
                    market_value_eur=random.uniform(500000, 50000000),
                    is_active=True,
                    consent_given=True
                )
                jersey_idx += 1

                players.append(player)
                session.add(player)

    await session.commit()
    print(f"✅ Created {len(players)} players across all teams")
    return players


async def create_matches(session: AsyncSession, org_id, season_id, teams: list[Team]) -> list[Match]:
    """Create sample matches."""
    matches = []
    match_date = date(2024, 9, 1)

    for week in range(15):  # 15 weeks of matches
        # Create 4 matches per week
        random.shuffle(teams)
        for i in range(0, min(8, len(teams)), 2):
            if i + 1 < len(teams):
                match = Match(
                    id=uuid4(),
                    organization_id=org_id,
                    season_id=season_id,
                    home_team_id=teams[i].id,
                    away_team_id=teams[i+1].id,
                    date=match_date,
                    venue=f"Stadium {teams[i].name}",
                    status="COMPLETED",
                    home_score=random.randint(0, 4),
                    away_score=random.randint(0, 4)
                )
                matches.append(match)
                session.add(match)

        match_date += timedelta(days=7)

    await session.commit()
    print(f"✅ Created {len(matches)} matches")
    return matches


async def generate_position_stats(position: PlayerRole) -> dict:
    """Generate realistic stats based on position."""
    base_stats = {
        "goals": 0,
        "assists": 0,
        "shots": 0,
        "shots_on_target": 0,
        "dribbles_attempted": 0,
        "dribbles_success": 0,
        "offsides": 0,
        "penalties_scored": 0,
        "penalties_missed": 0,
        "passes_attempted": 0,
        "passes_completed": 0,
        "key_passes": 0,
        "through_balls": 0,
        "crosses": 0,
        "cross_accuracy_pct": 0.0,
        "long_balls": 0,
        "long_balls_completed": 0,
        "tackles_attempted": 0,
        "tackles_success": 0,
        "interceptions": 0,
        "clearances": 0,
        "blocks": 0,
        "aerial_duels_won": 0,
        "aerial_duels_lost": 0,
        "duels_won": 0,
        "duels_lost": 0,
        "saves": 0,
        "saves_from_inside_box": 0,
        "punches": 0,
        "high_claims": 0,
        "catches": 0,
        "sweeper_clearances": 0,
        "throw_outs": 0,
        "goal_kicks": 0,
        "distance_covered_m": random.randint(8000, 12000),
        "sprints": random.randint(10, 40),
        "top_speed_kmh": random.uniform(28, 35),
        "fouls_committed": random.randint(0, 3),
        "fouls_suffered": random.randint(0, 4),
        "yellow_cards": 1 if random.random() > 0.85 else 0,
        "red_cards": 1 if random.random() > 0.98 else 0
    }

    if position == PlayerRole.GK:
        base_stats.update({
            "saves": random.randint(3, 10),
            "saves_from_inside_box": random.randint(1, 5),
            "punches": random.randint(0, 3),
            "high_claims": random.randint(2, 8),
            "catches": random.randint(3, 10),
            "goal_kicks": random.randint(10, 25),
            "passes_attempted": random.randint(20, 40),
            "passes_completed": random.randint(15, 35),
            "clearances": random.randint(2, 8),
            "distance_covered_m": random.randint(4000, 6000)
        })

    elif position == PlayerRole.DF:
        base_stats.update({
            "goals": 1 if random.random() > 0.9 else 0,
            "assists": 1 if random.random() > 0.85 else 0,
            "shots": random.randint(0, 2),
            "shots_on_target": random.randint(0, 1),
            "passes_attempted": random.randint(30, 70),
            "passes_completed": random.randint(25, 65),
            "tackles_attempted": random.randint(3, 10),
            "tackles_success": random.randint(2, 8),
            "interceptions": random.randint(2, 8),
            "clearances": random.randint(4, 12),
            "blocks": random.randint(1, 4),
            "aerial_duels_won": random.randint(2, 8),
            "aerial_duels_lost": random.randint(1, 4),
            "long_balls": random.randint(5, 15),
            "long_balls_completed": random.randint(3, 12)
        })

    elif position == PlayerRole.MF:
        base_stats.update({
            "goals": random.randint(0, 2),
            "assists": random.randint(0, 3),
            "shots": random.randint(1, 6),
            "shots_on_target": random.randint(0, 4),
            "dribbles_attempted": random.randint(3, 10),
            "dribbles_success": random.randint(2, 7),
            "passes_attempted": random.randint(40, 90),
            "passes_completed": random.randint(35, 80),
            "key_passes": random.randint(1, 6),
            "through_balls": random.randint(0, 3),
            "crosses": random.randint(2, 8),
            "cross_accuracy_pct": random.uniform(30, 70),
            "tackles_attempted": random.randint(2, 6),
            "tackles_success": random.randint(1, 5),
            "interceptions": random.randint(1, 5),
            "duels_won": random.randint(3, 10),
            "duels_lost": random.randint(2, 6)
        })

    elif position == PlayerRole.FW:
        base_stats.update({
            "goals": random.randint(0, 3),
            "assists": random.randint(0, 2),
            "shots": random.randint(2, 8),
            "shots_on_target": random.randint(1, 6),
            "dribbles_attempted": random.randint(4, 12),
            "dribbles_success": random.randint(2, 8),
            "offsides": random.randint(0, 3),
            "passes_attempted": random.randint(20, 50),
            "passes_completed": random.randint(15, 45),
            "key_passes": random.randint(0, 4),
            "aerial_duels_won": random.randint(1, 6),
            "aerial_duels_lost": random.randint(1, 4),
            "fouls_suffered": random.randint(2, 6)
        })

    return base_stats


async def create_player_stats(
    session: AsyncSession,
    org_id,
    players: list[Player],
    matches: list[Match]
):
    """Create detailed player statistics for matches with ML calculations."""
    print("🎯 Generating player statistics with ML metrics...")

    stats_count = 0

    for match in matches:
        # Get players from both teams
        home_players = [p for p in players if p.team_id == match.home_team_id]
        away_players = [p for p in players if p.team_id == match.away_team_id]

        # Select 11 starters + 3 subs per team
        selected_home = random.sample(home_players, min(14, len(home_players)))
        selected_away = random.sample(away_players, min(14, len(away_players)))

        all_match_players = selected_home + selected_away

        for player in all_match_players:
            # Generate position-specific stats
            stats_dict = await generate_position_stats(player.role_primary)

            # Create PlayerStats object
            player_stat = PlayerStats(
                id=uuid4(),
                player_id=player.id,
                match_id=match.id,
                organization_id=org_id,
                season="2024-2025",
                date=match.date,
                minutes_played=random.randint(60, 90),
                is_starter=random.random() > 0.3,
                **stats_dict
            )

            # Calculate efficiency metrics
            player_stat.calculate_efficiency_metrics()

            # Calculate ML metrics using our advanced algorithms
            player_stat.performance_index = advanced_ml.calculate_performance_index(
                player_stat, player.role_primary
            )
            player_stat.influence_score = advanced_ml.calculate_influence_score(player_stat)
            player_stat.expected_goals_xg = advanced_ml.calculate_expected_goals(
                player_stat, player.role_primary
            )
            player_stat.expected_assists_xa = advanced_ml.calculate_expected_assists(player_stat)

            session.add(player_stat)
            stats_count += 1

        # Commit every 50 stats to avoid memory issues
        if stats_count % 50 == 0:
            await session.commit()
            print(f"   Progress: {stats_count} stats created...")

    await session.commit()
    print(f"✅ Created {stats_count} player statistics with ML metrics")


async def update_player_ratings(session: AsyncSession, players: list[Player]):
    """Update player ratings based on their statistics."""
    print("📊 Updating player ratings...")

    for player in players:
        # Fetch player stats
        stmt = (
            select(PlayerStats)
            .where(PlayerStats.player_id == player.id)
            .order_by(PlayerStats.date.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        stats = result.scalars().all()

        if stats:
            # Calculate average performance
            avg_performance = sum(s.performance_index for s in stats) / len(stats)

            # Predict form
            form = await advanced_ml.predict_player_form(session, str(player.id), matches_to_analyze=5)

            # Update player
            player.overall_rating = min(10.0, max(5.0, avg_performance / 10))
            player.form_level = form

            # Calculate potential (younger players have higher potential)
            age = (datetime.now().date() - player.date_of_birth).days // 365
            if age <= 23:
                player.potential_rating = min(10.0, player.overall_rating + random.uniform(0.5, 2.0))
            else:
                player.potential_rating = min(10.0, player.overall_rating + random.uniform(0, 0.5))

            # Adjust market value based on performance
            age_factor = max(0.3, 1.0 - (age - 25) * 0.05) if age >= 25 else 1.0
            player.market_value_eur = (
                player.overall_rating ** 2.5 * 100000 * age_factor * random.uniform(0.8, 1.2)
            )

    await session.commit()
    print("✅ Player ratings and market values updated")


async def main():
    """Main seed function."""
    print("🚀 Starting complete database seeding with advanced analytics...\n")

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # 1. Create organization
            org = await create_organization(session)

            # 2. Create admin user
            await create_admin_user(session, org.id)

            # 3. Create season
            season = await create_season(session, org.id)

            # 4. Create teams
            teams = await create_teams(session, org.id)

            # 5. Create players
            players = await create_players(session, org.id, teams)

            # 6. Create matches
            matches = await create_matches(session, org.id, season.id, teams)

            # 7. Create player statistics with ML
            await create_player_stats(session, org.id, players, matches)

            # 8. Update player ratings
            await update_player_ratings(session, players)

            # Print summary
            print("\n" + "="*60)
            print("🎉 DATABASE SEEDING COMPLETED SUCCESSFULLY!")
            print("="*60)

            # Count records
            org_count = (await session.execute(select(func.count(Organization.id)))).scalar()
            team_count = (await session.execute(select(func.count(Team.id)))).scalar()
            player_count = (await session.execute(select(func.count(Player.id)))).scalar()
            match_count = (await session.execute(select(func.count(Match.id)))).scalar()
            stats_count = (await session.execute(select(func.count(PlayerStats.id)))).scalar()

            print(f"\n📊 DATA SUMMARY:")
            print(f"   • Organizations: {org_count}")
            print(f"   • Teams: {team_count}")
            print(f"   • Players: {player_count}")
            print(f"   • Matches: {match_count}")
            print(f"   • Player Statistics: {stats_count}")

            print(f"\n🔐 LOGIN CREDENTIALS:")
            print(f"   Email: admin@demo.club")
            print(f"   Password: admin123")

            print(f"\n🚀 NEXT STEPS:")
            print(f"   1. Start backend: uvicorn app.main:app --reload")
            print(f"   2. Visit API docs: http://localhost:8000/docs")
            print(f"   3. Test advanced analytics endpoints")
            print(f"   4. Check ADVANCED_ANALYTICS_GUIDE.md for API examples")

    except Exception as e:
        print(f"\n❌ ERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    from sqlalchemy import func
    exit_code = asyncio.run(main())
    exit(exit_code)

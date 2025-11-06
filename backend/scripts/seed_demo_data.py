"""
Seed demo data for EAV progress tracking.

Creates:
- 1 Season (2025/26)
- 1 Team (U17) with 25 players
- 90 days of wellness data per player
- 30 training sessions with attendance and metrics
- 8 matches with player stats and metrics
- Metric catalog entries
"""

import asyncio
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, async_session_maker
from app.models import (
    Season,
    Team,
    Player,
    Organization,
    TrainingSession,
    Match,
    Attendance,
)
from app.models.wellness_eav import WellnessSession, WellnessMetric
from app.models.training_eav import TrainingAttendance, TrainingMetric
from app.models.match_eav import MatchMetric, MatchPlayerPosition
from app.models.catalog import MetricCatalog


async def seed_metric_catalog(session: AsyncSession):
    """Seed metric catalog with common metrics (if not exists)."""
    print("🗂️  Seeding metric catalog...")

    # Check if already seeded
    result = await session.execute(text("SELECT COUNT(*) FROM metric_catalog"))
    count = result.scalar()

    if count > 0:
        print(f"   ℹ️  Metric catalog already has {count} entries, skipping...")
        return

    # Already seeded via migration
    print("   ✅ Metric catalog seeded via migration")


async def get_or_create_organization(session: AsyncSession) -> Organization:
    """Get first organization or create demo one."""
    print("🏢 Getting organization...")

    result = await session.execute(text("SELECT id FROM organizations LIMIT 1"))
    org_id = result.scalar_one_or_none()

    if org_id:
        org = await session.get(Organization, org_id)
        print(f"   ✅ Using existing organization: {org.name}")
        return org

    # Create demo org
    org = Organization(
        id=uuid4(),
        name="Demo Football Club",
        website="https://demo.club",
    )
    session.add(org)
    await session.flush()
    print(f"   ✅ Created demo organization: {org.name}")
    return org


async def seed_season_and_team(session: AsyncSession, org: Organization):
    """Create season and team."""
    print("⚽ Creating season and team...")

    # Check if already exists
    result = await session.execute(
        text("SELECT id FROM seasons WHERE name = '2025/26' AND organization_id = :org_id"),
        {"org_id": org.id}
    )
    season_id = result.scalar_one_or_none()

    if season_id:
        season = await session.get(Season, season_id)
        print(f"   ℹ️  Season {season.name} already exists")
    else:
        season = Season(
            id=uuid4(),
            name="2025/26",
            start_date=date(2025, 7, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
            organization_id=org.id,
        )
        session.add(season)
        await session.flush()
        print(f"   ✅ Created season: {season.name}")

    # Check if team exists
    result = await session.execute(
        text("SELECT id FROM teams WHERE name = 'U17' AND season_id = :season_id"),
        {"season_id": season.id}
    )
    team_id = result.scalar_one_or_none()

    if team_id:
        team = await session.get(Team, team_id)
        print(f"   ℹ️  Team {team.name} already exists")
    else:
        team = Team(
            id=uuid4(),
            name="U17",
            category="Youth",
            season_id=season.id,
            organization_id=org.id,
        )
        session.add(team)
        await session.flush()
        print(f"   ✅ Created team: {team.name}")

    return season, team


async def seed_players(session: AsyncSession, team: Team, org: Organization):
    """Create 2 players (GK and CM) if not exist."""
    print("👥 Creating players...")

    # Check existing players for this team with specific external_ids
    result = await session.execute(
        text("SELECT id FROM players WHERE team_id = :team_id AND external_id IN ('DEMO_GK_01', 'DEMO_CM_01')"),
        {"team_id": team.id}
    )
    existing_players = result.fetchall()
    
    if len(existing_players) >= 2:
        print(f"   ℹ️  Players already exist, using existing...")
        players = []
        for row in existing_players:
            p = await session.get(Player, row[0])
            players.append(p)
        return players

    # Create GK (Goalkeeper)
    gk = Player(
        id=uuid4(),
        external_id="DEMO_GK_01",
        first_name="Marco",
        last_name="Rossi",
        date_of_birth=date(2008, 3, 15),
        nationality="IT",
        role_primary="GK",
        height_cm=185,
        weight_kg=78,
        jersey_number=1,
        organization_id=org.id,
        team_id=team.id,
    )
    session.add(gk)
    
    # Create CM (Central Midfielder)
    cm = Player(
        id=uuid4(),
        external_id="DEMO_CM_01",
        first_name="Luca",
        last_name="Bianchi",
        date_of_birth=date(2008, 7, 22),
        nationality="IT",
        role_primary="MF",
        height_cm=175,
        weight_kg=68,
        jersey_number=8,
        organization_id=org.id,
        team_id=team.id,
    )
    session.add(cm)
    
    await session.flush()
    players = [gk, cm]
    print(f"   ✅ Created {len(players)} players: GK (Marco Rossi) and CM (Luca Bianchi)")
    return players


async def seed_wellness_data(session: AsyncSession, players: list[Player], org: Organization):
    """Create 90 days of wellness data for each player."""
    print("😴 Creating wellness data (90 days per player)...")

    today = date.today()

    # Check if wellness already seeded
    result = await session.execute(
        text("SELECT COUNT(*) FROM wellness_sessions WHERE player_id = :pid"),
        {"pid": players[0].id}
    )
    existing_count = result.scalar()

    if existing_count >= 80:  # If >80 entries exist, assume already seeded
        print(f"   ℹ️  Wellness data already seeded ({existing_count} sessions for first player), skipping...")
        return

    total_sessions = 0
    total_metrics = 0

    for player in players:
        for day_offset in range(90):
            session_date = today - timedelta(days=89 - day_offset)

            # Skip some days randomly (simulate missing data ~10%)
            if random.random() < 0.10:
                continue

            ws = WellnessSession(
                id=uuid4(),
                player_id=player.id,
                date=session_date,
                source="seed",
                organization_id=org.id,
            )
            session.add(ws)
            await session.flush()
            total_sessions += 1

            # Add metrics with some realistic variation
            base_sleep = random.uniform(6.5, 8.5)
            base_stress = random.uniform(3.0, 6.0)
            base_fatigue = random.uniform(3.0, 6.0)
            base_doms = random.uniform(2.0, 5.0)
            base_mood = random.uniform(6.0, 9.0)

            # Add temporal patterns (fatigue increases on training days)
            if day_offset % 7 in [1, 3, 5]:  # Training days pattern
                base_fatigue += random.uniform(1.0, 2.0)
                base_doms += random.uniform(0.5, 1.5)

            metrics_data = [
                ("sleep_hours", min(max(base_sleep - 1 + random.uniform(-0.5, 0.5), 4), 12), "hours"),
                ("sleep_quality", min(max(base_sleep + random.uniform(-0.5, 0.5), 1), 10), "score"),
                ("fatigue", min(max(base_fatigue + random.uniform(-1.0, 1.0), 1), 10), "score"),
                ("soreness", min(max(base_doms + random.uniform(-0.5, 0.5), 1), 10), "score"),
                ("stress", min(max(base_stress + random.uniform(-1.0, 1.0), 1), 10), "score"),
                ("mood", min(max(base_mood + random.uniform(-1.0, 1.0), 1), 10), "score"),
                ("motivation", min(max(random.uniform(6.0, 9.0), 1), 10), "score"),
                ("hydration", random.randint(6, 9), "score"),
                ("body_weight_kg", round(70 + random.uniform(-2, 2), 1), "kg"),
                ("resting_hr_bpm", random.randint(50, 65), "bpm"),
                ("hrv_ms", random.randint(40, 80), "ms"),
            ]

            for metric_key, value, unit in metrics_data:
                wm = WellnessMetric(
                    id=uuid4(),
                    wellness_session_id=ws.id,
                    metric_key=metric_key,
                    metric_value=round(value, 1),
                    unit=unit,
                )
                session.add(wm)
                total_metrics += 1

    await session.commit()
    print(f"   ✅ Created {total_sessions} wellness sessions with {total_metrics} metrics")


async def seed_training_sessions(session: AsyncSession, team: Team, players: list[Player], org: Organization):
    """Create 30 training sessions with attendance and metrics."""
    print("🏋️  Creating training sessions with attendance...")

    today = date.today()

    # Check if training sessions already seeded
    result = await session.execute(
        text("SELECT COUNT(*) FROM training_sessions WHERE team_id = :team_id"),
        {"team_id": team.id}
    )
    existing_count = result.scalar()

    if existing_count >= 25:
        print(f"   ℹ️  Training sessions already seeded ({existing_count}), skipping...")
        return

    total_sessions = 0
    total_attendance = 0
    total_metrics = 0

    session_types = ["technical", "tactical", "physical", "recovery"]
    locations = ["Main Field", "Training Ground A", "Gym"]

    for i in range(30):
        # Random date in last 85 days
        days_ago = random.randint(1, 85)
        session_date = datetime.combine(today - timedelta(days=days_ago), datetime.min.time())

        ts = TrainingSession(
            id=uuid4(),
            session_date=session_date,
            session_type=random.choice(["TRAINING", "TECHNICAL", "TACTICAL", "PHYSICAL"]),
            duration_min=random.choice([60, 75, 90, 105]),
            team_id=team.id,
            focus=random.choice(session_types),
            intensity=random.choice(["LOW", "MEDIUM", "HIGH"]),
            organization_id=org.id,
        )
        session.add(ts)
        await session.flush()
        total_sessions += 1

        # Add attendance for players (90% participation rate)
        for player in players:
            if random.random() < 0.90:  # 90% attendance
                minutes = random.choice([45, 60, 75, 90])
                rpe_post = random.randint(4, 8)

                att = TrainingAttendance(
                    id=uuid4(),
                    training_session_id=ts.id,
                    player_id=player.id,
                    status="present",
                    minutes=minutes,
                    participation_pct=int((minutes / ts.duration_min) * 100),
                    rpe_post=rpe_post,
                    organization_id=org.id,
                )
                session.add(att)
                await session.flush()
                total_attendance += 1

                # Add training metrics
                hsr = random.randint(150, 800)  # High Speed Running (m)
                total_distance = round(random.uniform(3.0, 9.0), 2)  # km
                accel_count = random.randint(15, 100)
                sprint_count = random.randint(5, 30)
                avg_hr = random.randint(140, 175)

                metrics_data = [
                    ("hsr", hsr, "m"),
                    ("total_distance", total_distance, "km"),
                    ("accel_count", accel_count, "#"),
                    ("sprint_count", sprint_count, "#"),
                    ("avg_hr", avg_hr, "bpm"),
                ]

                for metric_key, value, unit in metrics_data:
                    tm = TrainingMetric(
                        id=uuid4(),
                        training_attendance_id=att.id,
                        metric_key=metric_key,
                        metric_value=float(value),
                        unit=unit,
                    )
                    session.add(tm)
                    total_metrics += 1

    await session.commit()
    print(f"   ✅ Created {total_sessions} training sessions, {total_attendance} attendances, {total_metrics} metrics")


async def seed_matches(session: AsyncSession, team: Team, players: list[Player], org: Organization):
    """Create 6 matches with player stats and metrics."""
    print("⚽ Creating matches with player stats...")

    today = date.today()

    # Check if matches already seeded
    result = await session.execute(
        text("SELECT COUNT(*) FROM matches WHERE team_id = :team_id"),
        {"team_id": team.id}
    )
    existing_count = result.scalar()

    if existing_count >= 6:
        print(f"   ℹ️  Matches already seeded ({existing_count}), skipping...")
        return

    total_matches = 0
    total_attendances = 0
    total_metrics = 0

    opponents = ["Juventus U17", "Milan U17", "Inter U17", "Roma U17", "Napoli U17", "Lazio U17"]
    results = ["WIN", "DRAW", "LOSS"]

    for i in range(6):
        days_ago = random.randint(7, 80)
        match_date = datetime.combine(today - timedelta(days=days_ago), datetime.min.time())

        result = random.choice(results)
        if result == "WIN":
            goals_for, goals_against = random.randint(1, 4), random.randint(0, 2)
        elif result == "DRAW":
            goals = random.randint(0, 3)
            goals_for, goals_against = goals, goals
        else:  # LOSS
            goals_for, goals_against = random.randint(0, 2), random.randint(1, 4)

        match = Match(
            id=uuid4(),
            match_date=match_date,
            match_type="LEAGUE",
            team_id=team.id,
            opponent_name=opponents[i],
            is_home=random.choice([True, False]),
            goals_for=goals_for,
            goals_against=goals_against,
            result=result,
            venue="Home Stadium" if i % 2 == 0 else "Away Stadium",
            organization_id=org.id,
        )
        session.add(match)
        await session.flush()
        total_matches += 1

        # Select 11 starters + 5 bench
        starters = random.sample(players, 11)
        bench = random.sample([p for p in players if p not in starters], min(5, len(players) - 11))

        for player in starters + bench:
            is_starter = player in starters
            minutes = random.randint(60, 90) if is_starter else random.randint(0, 45)

            if minutes == 0:
                continue  # Skip if didn't play

            att = Attendance(
                id=uuid4(),
                match_id=match.id,
                player_id=player.id,
                is_starter=is_starter,
                minutes_played=minutes,
                jersey_number=player.jersey_number,
                goals=random.choice([0, 0, 0, 1]) if random.random() < 0.2 else 0,
                assists=random.choice([0, 0, 1]) if random.random() < 0.15 else 0,
                coach_rating=round(random.uniform(5.5, 8.5), 1),
                organization_id=org.id,
            )
            session.add(att)
            await session.flush()
            total_attendances += 1

            # Add match metrics
            sprint_count = random.randint(8, 35)
            hsr = random.randint(200, 1200)
            total_distance = round(random.uniform(5.0, 12.0), 2)
            pass_accuracy = random.randint(65, 95)
            pass_completed = random.randint(15, 80)
            duels_won = random.randint(3, 20)
            touches = random.randint(30, 100)

            # Match metrics
            metrics_data = [
                ("pass_accuracy", pass_accuracy, "%"),
                ("passes_completed", pass_completed, "#"),
                ("duels_won", duels_won, "#"),
                ("touches", touches, "#"),
                ("dribbles_success", random.randint(0, 8), "#"),
                ("interceptions", random.randint(0, 5), "#"),
                ("tackles", random.randint(0, 6), "#"),
                ("shots_on_target", random.randint(0, 3), "#"),
            ]
            
            # Tactical metrics (placeholder realistic values)
            if player.role_primary == "GK":
                # GK specific: more recoveries, fewer progressive passes
                tactical_metrics = [
                    ("pressures", random.randint(5, 15), "#"),
                    ("recoveries_def_third", random.randint(8, 20), "#"),
                    ("progressive_passes", random.randint(2, 8), "#"),
                    ("line_breaking_passes_conceded", random.randint(0, 3), "#"),
                    ("xthreat_contrib", round(random.uniform(0.1, 0.5), 2), "score"),
                ]
            else:
                # CM/field player: more progressive passes, pressures
                tactical_metrics = [
                    ("pressures", random.randint(15, 35), "#"),
                    ("recoveries_def_third", random.randint(2, 10), "#"),
                    ("progressive_passes", random.randint(8, 25), "#"),
                    ("line_breaking_passes_conceded", random.randint(1, 5), "#"),
                    ("xthreat_contrib", round(random.uniform(0.3, 1.2), 2), "score"),
                ]
            
            metrics_data.extend(tactical_metrics)

            for metric_key, value, unit in metrics_data:
                mm = MatchMetric(
                    id=uuid4(),
                    attendance_id=att.id,
                    metric_key=metric_key,
                    metric_value=float(value),
                    unit=unit,
                    organization_id=org.id,
                )
                session.add(mm)
                total_metrics += 1

            # Add position
            position_map = {"GK": "GK", "DF": random.choice(["CB", "RB", "LB"]),
                          "MF": random.choice(["CM", "CDM", "CAM"]), "FW": random.choice(["ST", "LW", "RW"])}
            position = position_map.get(player.role_primary, "MF")

            pos = MatchPlayerPosition(
                id=uuid4(),
                attendance_id=att.id,
                position=position,
                minute_start=0,
                minute_end=minutes,
                organization_id=org.id,
            )
            session.add(pos)

    await session.commit()
    print(f"   ✅ Created {total_matches} matches, {total_attendances} attendances, {total_metrics} metrics")


async def main():
    """Main seed function."""
    print("=" * 60)
    print("🌱 SEEDING DEMO DATA - EAV Progress Tracking")
    print("=" * 60)

    async with async_session_maker() as session:
        try:
            await seed_metric_catalog(session)

            org = await get_or_create_organization(session)

            season, team = await seed_season_and_team(session, org)

            players = await seed_players(session, team, org)

            await seed_wellness_data(session, players, org)

            await seed_training_sessions(session, team, players, org)

            await seed_matches(session, team, players, org)

            # Get summary counts
            wellness_result = await session.execute(text("SELECT COUNT(*) FROM wellness_metrics"))
            training_result = await session.execute(text("SELECT COUNT(*) FROM training_metrics"))
            match_result = await session.execute(text("SELECT COUNT(*) FROM match_metrics"))
            wellness_count = wellness_result.scalar() or 0
            training_count = training_result.scalar() or 0
            match_count = match_result.scalar() or 0
            total_eav = wellness_count + training_count + match_count
            
            print("=" * 60)
            print("✅ SEEDING COMPLETE!")
            print("=" * 60)
            print(f"Organization: {org.name}")
            print(f"Season: {season.name}")
            print(f"Team: {team.name} ({len(players)} players)")
            print("")
            print("📊 Summary by family:")
            print(f"   Wellness metrics: {wellness_count}")
            print(f"   Training metrics: {training_count}")
            print(f"   Match metrics: {match_count}")
            print(f"   Total EAV records: {total_eav}")
            print("")
            print("Next steps:")
            print("1. Start the API: make up (or docker compose up)")
            print("2. Test endpoints:")
            print(f"   GET /api/v1/players/{players[0].id}/overview?period=28d")
            print(f"   GET /api/v1/players/{players[0].id}/progress?families=wellness,training&grouping=week")
            print(f"   GET /api/v1/players/{players[0].id}/training-load?window_short=7&window_long=28")
            print(f"   GET /api/v1/players/{players[0].id}/match-summary?date_from={date.today() - timedelta(days=90)}")
            print("=" * 60)

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())

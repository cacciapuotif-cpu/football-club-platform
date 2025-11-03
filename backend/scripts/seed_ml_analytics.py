"""Seed script for ML analytics tables with synthetic data."""

import asyncio
import random
from datetime import date, timedelta
from uuid import uuid4, UUID
from dateutil.relativedelta import relativedelta

from app.database import get_session_context
from app.models.player import Player, PlayerRole
from app.models.organization import Organization
from app.models.analytics import (
    Match,
    TrainingSession,
    PlayerMatchStat,
    PlayerTrainingLoad,
    PlayerFeatureDaily,
)
from app.services.ml_analytics_service import train_all, predict_all
from sqlalchemy import select

random.seed(42)

ROLES = [PlayerRole.GK, PlayerRole.DF, PlayerRole.MF, PlayerRole.FW]


async def ensure_players(org_id: UUID, n: int = 24):
    """Ensure minimum number of players exist."""
    async with get_session_context() as session:
        result = await session.execute(
            select(Player).where(Player.organization_id == org_id, Player.is_active == True)
        )
        existing_players = result.scalars().all()
        existing_count = len(existing_players)

        to_create = max(0, n - existing_count)
        print(f"Found {existing_count} players, creating {to_create} more...")

        for i in range(to_create):
            role = random.choices(ROLES, weights=[1, 8, 8, 7])[0]
            player = Player(
                id=uuid4(),
                first_name=f"Player",
                last_name=f"{existing_count + i + 1}",
                date_of_birth=date(2000, 1, 1) + timedelta(days=random.randint(0, 3650)),
                role_primary=role,
                organization_id=org_id,
                consent_given=True,
                medical_clearance=True,
            )
            session.add(player)

        await session.commit()
        print(f"Players ready: {existing_count + to_create}")


async def seed_matches(org_id: UUID, start_date: date, end_date: date, per_week: int = 1):
    """Seed match data."""
    async with get_session_context() as session:
        matches = []
        days = (end_date - start_date).days
        step = 7 // max(1, per_week)

        for d in range(0, days, step * 7):
            match = Match(
                id=uuid4(),
                date=start_date + timedelta(days=d),
                opponent=f"Opponent-{random.randint(1, 20)}",
                competition="League",
                home=bool(random.getrandbits(1)),
                minutes=90,
                organization_id=org_id,
            )
            session.add(match)
            matches.append(match)

        await session.commit()
        print(f"Created {len(matches)} matches")
        return matches


async def seed_sessions(org_id: UUID, start_date: date, end_date: date):
    """Seed training sessions."""
    async with get_session_context() as session:
        sessions = []
        cur = start_date

        while cur <= end_date:
            if cur.weekday() in (0, 1, 3, 4):  # 4 sessions per week
                sess = TrainingSession(
                    id=uuid4(),
                    date=cur,
                    session_type=random.choice(["strength", "endurance", "tactical", "mixed"]),
                    duration_min=random.randint(60, 110),
                    rpe=round(random.uniform(4.0, 7.5), 2),
                    organization_id=org_id,
                )
                session.add(sess)
                sessions.append(sess)
            cur += timedelta(days=1)

        await session.commit()
        print(f"Created {len(sessions)} training sessions")
        return sessions


def role_profile(role: PlayerRole):
    """Get statistical profile based on role."""
    if role == PlayerRole.FW:
        return dict(xg=0.35, shots=3, key_passes=2, duels=5, sprints=18)
    if role == PlayerRole.MF:
        return dict(xg=0.15, shots=1, key_passes=3, duels=7, sprints=12)
    if role == PlayerRole.DF:
        return dict(xg=0.05, shots=0, key_passes=1, duels=9, sprints=8)
    return dict(xg=0.01, shots=0, key_passes=0, duels=3, sprints=3)  # GK


async def seed_player_stats(org_id: UUID):
    """Seed player match statistics."""
    async with get_session_context() as session:
        # Get all players
        players_result = await session.execute(
            select(Player.id, Player.role_primary).where(
                Player.organization_id == org_id, Player.is_active == True
            )
        )
        players = players_result.all()

        # Get all matches
        matches_result = await session.execute(
            select(Match).where(Match.organization_id == org_id).order_by(Match.date)
        )
        matches = matches_result.scalars().all()

        count = 0
        for match in matches:
            for pid, role in players:
                prof = role_profile(role)
                stat = PlayerMatchStat(
                    id=uuid4(),
                    player_id=pid,
                    match_id=match.id,
                    minutes=90 if role != PlayerRole.GK else 90,
                    goals=1 if (role == PlayerRole.FW and random.random() < 0.3) else 0,
                    assists=1 if random.random() < 0.15 else 0,
                    shots=max(0, int(random.gauss(prof["shots"], 1))),
                    xg=max(0, round(random.gauss(prof["xg"], 0.1), 3)),
                    key_passes=max(0, int(random.gauss(prof["key_passes"], 1))),
                    duels_won=max(0, int(random.gauss(prof["duels"], 2))),
                    sprints=max(0, int(random.gauss(prof["sprints"], 4))),
                    pressures=max(0, int(random.gauss(10, 3))),
                    def_actions=max(0, int(random.gauss(8 if role in (PlayerRole.DF, PlayerRole.MF) else 3, 2))),
                    organization_id=org_id,
                )
                session.add(stat)
                count += 1

        await session.commit()
        print(f"Created {count} player match stats")


async def seed_training_loads(org_id: UUID):
    """Seed player training load data."""
    async with get_session_context() as session:
        # Get all players
        players_result = await session.execute(
            select(Player.id).where(Player.organization_id == org_id, Player.is_active == True)
        )
        players = [row[0] for row in players_result.all()]

        # Get all sessions
        sessions_result = await session.execute(
            select(TrainingSession).where(TrainingSession.organization_id == org_id)
        )
        sessions = sessions_result.scalars().all()

        count = 0
        for sess in sessions:
            for pid in players:
                ac = round(random.uniform(200, 800), 1)
                ch = round(random.uniform(300, 900), 1)
                mono = round(random.uniform(1.0, 3.0), 2)
                strain = round(ac * mono, 2)
                inj_hist = bool(random.random() < 0.1)

                load = PlayerTrainingLoad(
                    id=uuid4(),
                    player_id=pid,
                    session_id=sess.id,
                    load_acute=ac,
                    load_chronic=ch,
                    monotony=mono,
                    strain=strain,
                    injury_history_flag=inj_hist,
                    organization_id=org_id,
                )
                session.add(load)
                count += 1

        await session.commit()
        print(f"Created {count} training load records")


async def seed_features_daily(org_id: UUID, start_date: date, end_date: date):
    """Seed daily player features."""
    async with get_session_context() as session:
        # Get all players
        players_result = await session.execute(
            select(Player.id).where(Player.organization_id == org_id, Player.is_active == True)
        )
        players = [row[0] for row in players_result.all()]

        count = 0
        for pid in players:
            cur = start_date
            r7 = 0.0
            r21 = 0.0

            while cur <= end_date:
                r7 = max(0.0, r7 + random.uniform(-10, 10))
                r21 = max(0.0, r21 + random.uniform(-5, 15))
                form = max(0.0, min(1.0, random.gauss(0.5, 0.2)))

                feat = PlayerFeatureDaily(
                    id=uuid4(),
                    player_id=pid,
                    date=cur,
                    rolling_7d_load=round(r7, 2),
                    rolling_21d_load=round(r21, 2),
                    form_score=round(form, 3),
                    injury_flag=bool(random.random() < 0.05),
                    organization_id=org_id,
                )
                session.add(feat)
                count += 1
                cur += timedelta(days=1)

        await session.commit()
        print(f"Created {count} daily feature records")


async def main():
    """Main seed function."""
    print("=" * 60)
    print("ML Analytics Advanced Seed Script")
    print("=" * 60)

    # Get or create organization
    async with get_session_context() as session:
        org_result = await session.execute(select(Organization).limit(1))
        org = org_result.scalar_one_or_none()

        if not org:
            print("Creating default organization...")
            org = Organization(
                id=uuid4(),
                name="Football Club Platform",
                slug="football-club",
                is_active=True,
            )
            session.add(org)
            await session.commit()
            print(f"Organization created: {org.name}")
        else:
            print(f"Using existing organization: {org.name}")

        org_id = org.id

    # Ensure players
    await ensure_players(org_id, n=24)

    # Date range: last 4 months
    end = date.today()
    start = end - relativedelta(months=4)
    print(f"Date range: {start} to {end}")

    # Seed data
    await seed_matches(org_id, start, end, per_week=1)
    await seed_sessions(org_id, start, end)
    await seed_player_stats(org_id)
    await seed_training_loads(org_id)
    await seed_features_daily(org_id, start, end)

    print("\n" + "=" * 60)
    print("Training ML models...")
    print("=" * 60)
    result = await train_all()
    print(f"Training result: {result}")

    print("\n" + "=" * 60)
    print("Generating predictions for all players...")
    print("=" * 60)
    count = await predict_all(org_id)
    print(f"Generated {count} predictions")

    print("\n" + "=" * 60)
    print("Seed completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

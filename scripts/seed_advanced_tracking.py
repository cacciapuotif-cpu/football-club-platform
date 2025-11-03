"""Seed script for advanced tracking models with sample data."""

import asyncio
import json
import random
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.config import settings
from app.models.advanced_tracking import (
    AutomatedInsight,
    DailyReadiness,
    GoalCategory,
    GoalStatus,
    InsightPriority,
    InsightType,
    MatchPlayerStats,
    PerformanceSnapshot,
    PlayerGoal,
)
from app.models.match import Match
from app.models.organization import Organization
from app.models.player import Player
from app.models.team import Team


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def seed_performance_snapshots(session: AsyncSession):
    """Seed performance snapshots data."""
    print("Seeding performance snapshots...")

    # Get first org and players
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        print("No organization found. Skipping snapshots.")
        return

    result = await session.execute(
        select(Player).where(Player.organization_id == org.id).limit(3)
    )
    players = result.scalars().all()

    snapshots_created = 0
    for player in players:
        # Create weekly snapshots for last 3 months
        for weeks_ago in range(12):
            snapshot_date = date.today() - timedelta(weeks=weeks_ago)

            # Simulate improving trend
            trend_factor = 1 + (12 - weeks_ago) * 0.02  # Gradual improvement

            snapshot = PerformanceSnapshot(
                player_id=player.id,
                snapshot_date=snapshot_date,
                period_type="WEEKLY",
                physical_score=random.uniform(65, 85) * trend_factor,
                technical_score=random.uniform(60, 80) * trend_factor,
                tactical_score=random.uniform(55, 75) * trend_factor,
                psychological_score=random.uniform(70, 90),
                health_score=random.uniform(75, 95),
                overall_score=random.uniform(65, 85) * trend_factor,
                form_index=random.uniform(60, 80) * trend_factor,
                physical_percentile=random.uniform(50, 90),
                technical_percentile=random.uniform(45, 85),
                tactical_percentile=random.uniform(40, 80),
                team_rank_physical=random.randint(3, 15),
                team_rank_technical=random.randint(5, 18),
                team_rank_overall=random.randint(4, 16),
                physical_zscore=random.uniform(-0.5, 1.5),
                technical_zscore=random.uniform(-0.3, 1.2),
                tactical_zscore=random.uniform(-0.4, 1.0),
                trend_3m=1 if weeks_ago < 6 else 0,
                trend_6m=1,
                metrics_summary=json.dumps({
                    "avg_distance_km": round(random.uniform(8.5, 11.5), 1),
                    "avg_sprints": random.randint(15, 35),
                    "avg_pass_accuracy": round(random.uniform(75, 88), 1)
                }),
                notes=f"Settimana {12-weeks_ago}/12: Performance {'in crescita' if weeks_ago < 6 else 'stabile'}",
                organization_id=org.id
            )
            session.add(snapshot)
            snapshots_created += 1

    await session.commit()
    print(f"✓ Created {snapshots_created} performance snapshots")


async def seed_player_goals(session: AsyncSession):
    """Seed player goals data."""
    print("Seeding player goals...")

    # Get first org and players
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        print("No organization found. Skipping goals.")
        return

    result = await session.execute(
        select(Player).where(Player.organization_id == org.id).limit(3)
    )
    players = result.scalars().all()

    goals_created = 0
    goal_templates = [
        {
            "category": GoalCategory.TECHNICAL,
            "title": "Aumentare precisione passaggi",
            "metric": "pass_accuracy_pct",
            "baseline": 78.5,
            "target": 85.0,
            "unit": "%"
        },
        {
            "category": GoalCategory.PHYSICAL,
            "title": "Migliorare velocità sprint 20m",
            "metric": "sprint_20m_s",
            "baseline": 3.2,
            "target": 2.95,
            "unit": "s"
        },
        {
            "category": GoalCategory.TACTICAL,
            "title": "Aumentare decisioni corrette",
            "metric": "correct_decisions_pct",
            "baseline": 65.0,
            "target": 75.0,
            "unit": "%"
        },
        {
            "category": GoalCategory.PSYCHOLOGICAL,
            "title": "Migliorare leadership",
            "metric": "leadership_rating",
            "baseline": 3,
            "target": 4,
            "unit": "/5"
        }
    ]

    for player in players:
        # Create 2-3 goals per player
        for template in random.sample(goal_templates, k=random.randint(2, 3)):
            start_date = date.today() - timedelta(days=random.randint(20, 40))
            target_date = start_date + timedelta(weeks=8)
            days_passed = (date.today() - start_date).days
            total_days = (target_date - start_date).days

            # Simulate progress
            progress_pct = min(95, (days_passed / total_days) * 100 * random.uniform(0.8, 1.2))
            current_value = template["baseline"] + (template["target"] - template["baseline"]) * (progress_pct / 100)

            # Determine status
            if progress_pct >= 100:
                status = GoalStatus.COMPLETED
            elif progress_pct > 10:
                status = GoalStatus.IN_PROGRESS
            else:
                status = GoalStatus.NOT_STARTED

            goal = PlayerGoal(
                player_id=player.id,
                category=template["category"],
                status=status,
                title=template["title"],
                description=f"Obiettivo SMART per migliorare {template['metric']} in 8 settimane",
                metric_name=template["metric"],
                baseline_value=template["baseline"],
                target_value=template["target"],
                current_value=current_value,
                unit=template["unit"],
                start_date=start_date,
                target_date=target_date,
                completed_date=target_date if status == GoalStatus.COMPLETED else None,
                progress_pct=progress_pct,
                days_remaining=max(0, (target_date - date.today()).days),
                on_track=progress_pct >= (days_passed / total_days) * 100 * 0.9,
                milestones=json.dumps([
                    {"week": 2, "target": template["baseline"] + (template["target"] - template["baseline"]) * 0.25, "completed": days_passed > 14},
                    {"week": 4, "target": template["baseline"] + (template["target"] - template["baseline"]) * 0.50, "completed": days_passed > 28},
                    {"week": 6, "target": template["baseline"] + (template["target"] - template["baseline"]) * 0.75, "completed": days_passed > 42}
                ]),
                predicted_completion_probability=random.uniform(0.65, 0.92),
                predicted_final_value=template["baseline"] + (template["target"] - template["baseline"]) * random.uniform(0.85, 1.1),
                coach_notes="Monitora progress settimanale. Buon impegno.",
                organization_id=org.id
            )
            session.add(goal)
            goals_created += 1

    await session.commit()
    print(f"✓ Created {goals_created} player goals")


async def seed_match_player_stats(session: AsyncSession):
    """Seed match player stats data."""
    print("Seeding match player stats...")

    # Get first org
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        print("No organization found. Skipping match stats.")
        return

    result = await session.execute(
        select(Player).where(Player.organization_id == org.id).limit(5)
    )
    players = result.scalars().all()

    # Get or create sample match
    result = await session.execute(
        select(Match).where(Match.organization_id == org.id).limit(1)
    )
    match = result.scalar_one_or_none()
    if not match:
        # Create a sample match
        result = await session.execute(select(Team).where(Team.organization_id == org.id).limit(1))
        team = result.scalar_one_or_none()
        if team:
            match = Match(
                match_date=date.today() - timedelta(days=7),
                home_team_id=team.id,
                away_team_id=team.id,  # Dummy
                competition="Serie D",
                match_type="LEAGUE",
                home_score=2,
                away_score=1,
                organization_id=org.id
            )
            session.add(match)
            await session.commit()
            await session.refresh(match)

    if not match:
        print("No match found. Skipping match stats.")
        return

    stats_created = 0
    for player in players:
        minutes = random.choice([90, 90, 75, 60, 45, 30])
        started = minutes >= 70

        stats = MatchPlayerStats(
            player_id=player.id,
            match_id=match.id,
            match_date=match.match_date,
            minutes_played=minutes,
            started=started,
            substituted_in_min=0 if started else random.randint(1, 60),
            substituted_out_min=None if minutes == 90 else minutes,
            yellow_cards=random.choice([0, 0, 0, 1]),
            red_cards=0,
            distance_m=random.uniform(7500, 11500),
            hi_distance_m=random.uniform(800, 1500),
            sprints_count=random.randint(12, 35),
            top_speed_kmh=random.uniform(28, 34),
            accelerations=random.randint(25, 50),
            decelerations=random.randint(20, 45),
            passes_completed=random.randint(25, 65),
            passes_attempted=random.randint(30, 75),
            pass_accuracy_pct=random.uniform(75, 92),
            key_passes=random.randint(0, 5),
            assists=random.choice([0, 0, 0, 1]),
            shots=random.randint(0, 4),
            shots_on_target=random.randint(0, 2),
            goals=random.choice([0, 0, 0, 0, 1]),
            dribbles_completed=random.randint(0, 5),
            dribbles_attempted=random.randint(1, 8),
            crosses_completed=random.randint(0, 3),
            crosses_attempted=random.randint(0, 6),
            tackles=random.randint(2, 8),
            interceptions=random.randint(1, 6),
            clearances=random.randint(0, 5),
            blocks=random.randint(0, 3),
            duels_won=random.randint(3, 12),
            duels_lost=random.randint(2, 8),
            fouls_committed=random.randint(0, 2),
            fouls_won=random.randint(0, 3),
            xg=random.uniform(0, 1.5),
            xa=random.uniform(0, 0.8),
            touches=random.randint(40, 90),
            possession_won=random.randint(5, 15),
            possession_lost=random.randint(3, 12),
            opponent_team="FC Avversario",
            opponent_difficulty=random.randint(5, 8),
            coach_rating=random.uniform(6.0, 8.5),
            team_avg_rating=random.uniform(6.5, 7.5),
            performance_index=random.uniform(65, 85),
            stats_by_half=json.dumps({
                "first_half": {"minutes": 45, "distance_m": random.uniform(3500, 5500)},
                "second_half": {"minutes": minutes - 45 if minutes > 45 else 0, "distance_m": random.uniform(3500, 5500)}
            }),
            notes="Buona prestazione complessiva" if random.random() > 0.5 else None,
            organization_id=org.id
        )
        session.add(stats)
        stats_created += 1

    await session.commit()
    print(f"✓ Created {stats_created} match player stats")


async def seed_daily_readiness(session: AsyncSession):
    """Seed daily readiness scores."""
    print("Seeding daily readiness scores...")

    # Get first org and players
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        print("No organization found. Skipping readiness.")
        return

    result = await session.execute(
        select(Player).where(Player.organization_id == org.id).limit(3)
    )
    players = result.scalars().all()

    readiness_created = 0
    for player in players:
        # Create daily readiness for last 14 days
        for days_ago in range(14):
            readiness_date = date.today() - timedelta(days=days_ago)

            # Simulate varying readiness
            base_readiness = random.uniform(55, 90)
            sleep_hours = random.uniform(6.5, 9.0)
            hrv = random.uniform(50, 85)

            readiness = DailyReadiness(
                player_id=player.id,
                date=readiness_date,
                readiness_score=base_readiness,
                sleep_score=random.uniform(60, 95),
                hrv_score=random.uniform(55, 90),
                recovery_score=random.uniform(60, 90),
                wellness_score=random.uniform(65, 92),
                workload_score=random.uniform(70, 95),
                sleep_hours=sleep_hours,
                sleep_quality=random.randint(3, 5),
                hrv_ms=hrv,
                resting_hr_bpm=random.randint(48, 65),
                doms_rating=random.randint(1, 4),
                fatigue_rating=random.randint(1, 4),
                stress_rating=random.randint(1, 3),
                mood_rating=random.randint(6, 9),
                yesterday_training_load=random.uniform(300, 800),
                acute_chronic_ratio=random.uniform(0.85, 1.25),
                recommended_training_intensity="HIGH" if base_readiness >= 75 else "MODERATE" if base_readiness >= 60 else "LOW",
                can_train_full=base_readiness >= 65,
                injury_risk_flag=base_readiness < 50,
                predicted_performance_today=base_readiness * random.uniform(0.9, 1.1),
                injury_risk_probability=max(0, (80 - base_readiness) / 80),
                coach_override=False,
                organization_id=org.id
            )
            session.add(readiness)
            readiness_created += 1

    await session.commit()
    print(f"✓ Created {readiness_created} daily readiness scores")


async def seed_automated_insights(session: AsyncSession):
    """Seed automated insights."""
    print("Seeding automated insights...")

    # Get first org and players
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        print("No organization found. Skipping insights.")
        return

    result = await session.execute(
        select(Player).where(Player.organization_id == org.id).limit(3)
    )
    players = result.scalars().all()

    insights_created = 0

    insight_templates = [
        {
            "type": InsightType.PERFORMANCE_DROP,
            "priority": InsightPriority.HIGH,
            "category": "PERFORMANCE",
            "title_template": "{name}: Calo pass accuracy -12%",
            "description": "Giocatore mostra calo significativo in pass accuracy ultimi 7 giorni. Media attuale: 76.2%, baseline: 86.5%. Calo del 12%.",
            "recommendation": "Verificare wellness recente, carico allenamenti, colloquio con giocatore."
        },
        {
            "type": InsightType.INJURY_RISK,
            "priority": InsightPriority.CRITICAL,
            "category": "INJURY",
            "title_template": "{name}: Rischio Infortunio 78%",
            "description": "Rischio infortunio elevato (78%). Fattori: HRV basso, carico alto, recupero insufficiente.",
            "recommendation": "Ridurre intensità per 48-72h, sessione recupero, valutazione medica se necessario."
        },
        {
            "type": InsightType.WELLNESS_ALERT,
            "priority": InsightPriority.MEDIUM,
            "category": "WELLNESS",
            "title_template": "{name}: Alert Wellness (sonno, stress)",
            "description": "Valori wellness preoccupanti ultimi 7 giorni. Sonno medio: 6.2h (ottimale >7.5h), stress medio: 3.8/5.",
            "recommendation": "Colloquio individuale, valutare riduzione carico, supporto psicologico."
        },
        {
            "type": InsightType.PERFORMANCE_PEAK,
            "priority": InsightPriority.LOW,
            "category": "PERFORMANCE",
            "title_template": "{name}: Picco Performance in sprint!",
            "description": "Giocatore ha raggiunto picco performance in velocità sprint. Valore: 32.8 km/h, percentile 95º. Uno dei migliori risultati!",
            "recommendation": "Complimenti! Analizzare fattori che hanno contribuito al picco per replicare successo."
        }
    ]

    for player in players:
        # Create 1-2 insights per player
        for template in random.sample(insight_templates, k=random.randint(1, 2)):
            insight = AutomatedInsight(
                player_id=player.id,
                team_id=player.team_id,
                insight_type=template["type"],
                priority=template["priority"],
                category=template["category"],
                title=template["title_template"].format(name=f"{player.first_name} {player.last_name}"),
                description=template["description"],
                actionable_recommendation=template["recommendation"],
                supporting_data=json.dumps({
                    "metric": "example_metric",
                    "current_value": random.uniform(60, 90),
                    "baseline": random.uniform(70, 95)
                }),
                confidence_score=random.uniform(0.75, 0.95),
                statistical_significance=random.uniform(0.01, 0.05),
                date_from=date.today() - timedelta(days=7),
                date_to=date.today(),
                is_active=True,
                is_read=random.choice([True, False]),
                dismissed=False,
                organization_id=org.id
            )
            session.add(insight)
            insights_created += 1

    await session.commit()
    print(f"✓ Created {insights_created} automated insights")


async def main():
    """Run all seed functions."""
    print("\n🌱 Starting advanced tracking seed script...")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            await seed_performance_snapshots(session)
            await seed_player_goals(session)
            await seed_match_player_stats(session)
            await seed_daily_readiness(session)
            await seed_automated_insights(session)

            print("=" * 60)
            print("✅ Advanced tracking seed completed successfully!\n")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())

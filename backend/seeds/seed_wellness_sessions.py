"""
Comprehensive Sessions & Wellness seed generator.

Creates multi-tenant demo data with 90 days of sessions, wellness, features,
predictions, and alerts aligned with Team B requirements.
"""

from __future__ import annotations

import asyncio
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

# Ensure backend is on path when executed as script
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.database import async_session_maker, set_rls_context
from app.models.organization import Organization
from app.models.player import Player, PlayerRole
from app.models.sessions_wellness import (
    Alert,
    AlertStatus,
    Athlete,
    Prediction,
    PredictionSeverity,
    Session,
    SessionParticipation,
    SessionParticipationStatus,
    SessionType,
    WellnessReading,
    Feature,
)
from app.models.team import Team

TENANT_CONFIG = [
    {
        "slug": "demo-fc",
        "name": "Demo Football Club",
        "city": "Roma",
        "country": "IT",
        "teams": [
            ("Primavera", "U19"),
            ("U18 Elite", "U18"),
            ("U17 Elite", "U17"),
            ("U16 Academy", "U16"),
        ],
    },
    {
        "slug": "aurora-academy",
        "name": "Aurora Academy",
        "city": "Torino",
        "country": "IT",
        "teams": [
            ("U19 Aurora", "U19"),
            ("U18 Aurora", "U18"),
            ("U17 Aurora", "U17"),
            ("U16 Aurora", "U16"),
        ],
    },
]

AGE_RANGE = (15, 17)
DAYS_BACK = 90
TARGET_PLAYERS_PER_TEAM = 8


@dataclass
class AthleteContext:
    player: Player
    athlete_id: UUID
    baseline_hrv: float
    baseline_sleep: float


def _random_name(seed_text: str) -> tuple[str, str]:
    random.seed(seed_text)
    first_names = ["Luca", "Matteo", "Giorgio", "Nicolo", "Alessio", "Davide", "Filippo", "Edoardo", "Riccardo"]
    last_names = ["Rossi", "Bianchi", "Verdi", "Romano", "Ferrari", "Marchetti", "Conti", "Santoro", "Moretti"]
    return random.choice(first_names), random.choice(last_names)


def _generate_birthdate(age: int) -> date:
    today = datetime.now(timezone.utc).date()
    year = today.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


async def ensure_organization(session: AsyncSession, slug: str, name: str, city: str, country: str) -> Organization:
    result = await session.execute(select(Organization).where(col(Organization.slug) == slug))
    org = result.scalar_one_or_none()
    if org:
        return org

    org = Organization(
        name=name,
        slug=slug,
        city=city,
        country=country,
        email=f"info@{slug}.it",
        benchmark_opt_in=True,
    )
    session.add(org)
    await session.flush()
    return org


async def ensure_team(session: AsyncSession, org: Organization, team_name: str, category: str) -> Team:
    result = await session.execute(
        select(Team).where(col(Team.organization_id) == org.id, col(Team.name) == team_name)
    )
    team = result.scalar_one_or_none()
    if team:
        return team

    team = Team(
        organization_id=org.id,
        name=team_name,
        category=category,
    )
    session.add(team)
    await session.flush()
    return team


async def ensure_players(
    session: AsyncSession,
    org: Organization,
    team: Team,
    target_players: int,
) -> list[Player]:
    result = await session.execute(
        select(Player).where(col(Player.organization_id) == org.id, col(Player.team_id) == team.id)
    )
    players = list(result.scalars().all())

    roles_cycle = [PlayerRole.GK, PlayerRole.DF, PlayerRole.MF, PlayerRole.FW]
    while len(players) < target_players:
        idx = len(players) + 1
        external_id = f"seed-{org.slug}-{team.name}-{idx}"
        result = await session.execute(select(Player).where(col(Player.external_id) == external_id))
        existing = result.scalar_one_or_none()
        if existing:
            players.append(existing)
            continue

        role = roles_cycle[idx % len(roles_cycle)]
        first_name, last_name = _random_name(f"{external_id}-name")
        age = random.randint(*AGE_RANGE)
        birth_date = _generate_birthdate(age)
        player = Player(
            external_id=external_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birth_date,
            nationality="IT",
            is_minor=True,
            guardian_name=f"{last_name} Guardian",
            guardian_email=f"{first_name.lower()}.{last_name.lower()}@example.com",
            guardian_phone="+39 320 0000000",
            role_primary=role,
            dominant_foot="RIGHT",
            dominant_arm="RIGHT",
            jersey_number=idx + 10,
            height_cm=175 + random.randint(-5, 8),
            weight_kg=68 + random.randint(-4, 6),
            organization_id=org.id,
            team_id=team.id,
            consent_given=True,
            medical_clearance=True,
            is_active=True,
        )
        session.add(player)
        await session.flush()
        players.append(player)

    return players


async def ensure_athletes(session: AsyncSession, org: Organization, players: Iterable[Player]) -> list[AthleteContext]:
    contexts: list[AthleteContext] = []
    for player in players:
        deterministic_id = uuid5(NAMESPACE_DNS, f"athlete-{player.id}")
        result = await session.execute(
            select(Athlete).where(col(Athlete.athlete_id) == deterministic_id, col(Athlete.tenant_id) == org.id)
        )
        athlete = result.scalar_one_or_none()
        if not athlete:
            athlete = Athlete(
                athlete_id=deterministic_id,
                tenant_id=org.id,
                player_id=player.id,
                pii_token=f"token-{player.id}",
            )
            session.add(athlete)
            await session.flush()
        elif athlete.player_id is None:
            athlete.player_id = player.id

        baseline_hrv = random.uniform(75, 110)
        baseline_sleep = random.uniform(7.5, 8.5)
        contexts.append(AthleteContext(player=player, athlete_id=athlete.athlete_id, baseline_hrv=baseline_hrv, baseline_sleep=baseline_sleep))
    return contexts


def _session_id(tenant: UUID, team: UUID, session_date: date, session_type: SessionType) -> UUID:
    seed_text = f"{tenant}-{team}-{session_date.isoformat()}-{session_type.value}"
    return uuid5(NAMESPACE_DNS, seed_text)


def _alert_id(tenant: UUID, athlete: UUID, event_date: date, policy: str) -> UUID:
    return uuid5(NAMESPACE_DNS, f"alert-{tenant}-{athlete}-{event_date.isoformat()}-{policy}")


def _prediction_id(tenant: UUID, athlete: UUID, event_date: date) -> UUID:
    return uuid5(NAMESPACE_DNS, f"prediction-{tenant}-{athlete}-{event_date.isoformat()}")


async def seed_tenant_data(session: AsyncSession, org: Organization) -> None:
    today = datetime.now(timezone.utc).date()
    start_day = today - timedelta(days=DAYS_BACK)
    tenants_created_alerts = 0

    for team_name, category in next(cfg for cfg in TENANT_CONFIG if cfg["slug"] == org.slug)["teams"]:
        team = await ensure_team(session, org, team_name, category)
        players = await ensure_players(session, org, team, TARGET_PLAYERS_PER_TEAM)
        athlete_contexts = await ensure_athletes(session, org, players)

        # container for features computation
        daily_metrics: dict[UUID, list[dict]] = defaultdict(list)

        for day_offset in range(DAYS_BACK):
            current_date = start_day + timedelta(days=day_offset)
            weekday = current_date.weekday()

            # Determine session type
            session_type = None
            if weekday in {0, 2, 4}:  # Mon/Wed/Fri training
                session_type = SessionType.TRAINING
            elif weekday == 5:  # Saturday match
                session_type = SessionType.MATCH
            elif weekday == 1:  # Tuesday recovery or gym
                session_type = SessionType.RECOVERY

            if session_type:
                start_ts = datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=16)
                end_ts = start_ts + timedelta(hours=2)
                session_uuid = _session_id(org.id, team.id, current_date, session_type)

                session_obj = await session.get(Session, session_uuid)
                if not session_obj:
                    base_load = {
                        SessionType.TRAINING: random.uniform(350, 480),
                        SessionType.MATCH: random.uniform(500, 650),
                        SessionType.RECOVERY: random.uniform(150, 250),
                    }[session_type]

                    # Weekly cycles (higher load mid-cycle)
                    if (day_offset // 7) % 3 == 1:
                        base_load *= 1.15

                    session_obj = Session(
                        session_id=session_uuid,
                        tenant_id=org.id,
                        team_id=team.id,
                        type=session_type,
                        start_ts=start_ts,
                        end_ts=end_ts,
                        rpe_avg=round(base_load / 100, 2),
                        load=round(base_load, 2),
                        notes=f"{session_type.value.title()} session auto-generated",
                    )
                    session.add(session_obj)

                for ctx in athlete_contexts:
                    participation_id = uuid5(NAMESPACE_DNS, f"sp-{session_obj.session_id}-{ctx.athlete_id}")
                    existing = await session.get(SessionParticipation, participation_id)
                    if existing:
                        continue

                    load_factor = random.uniform(0.9, 1.1)
                    travel_penalty = 1.0
                    if (day_offset // 14) % 2 == 0 and session_type == SessionType.MATCH:
                        travel_penalty = 1.1
                    adjusted_load = (session_obj.load or 0) * load_factor * travel_penalty
                    rpe = min(10.0, max(3.0, adjusted_load / 70))

                    session_part = SessionParticipation(
                        id=participation_id,
                        tenant_id=org.id,
                        session_id=session_obj.session_id,
                        athlete_id=ctx.athlete_id,
                        rpe=round(rpe, 2),
                        load=round(adjusted_load, 2),
                        status=SessionParticipationStatus.COMPLETED,
                    )
                    session.add(session_part)

                    daily_metrics[ctx.athlete_id].append(
                        {
                            "date": current_date,
                            "load": adjusted_load,
                        }
                    )

            # Wellness metrics (daily)
            for ctx in athlete_contexts:
                fatigue_spike = 0.0
                illness_factor = 0.0
                if day_offset in {20, 21, 22, 60, 61}:
                    fatigue_spike = 1.5
                if (day_offset // 21) % 4 == 3:
                    illness_factor = 1.2 if weekday in {0, 1} else 0.0

                sleep = max(5.0, random.gauss(ctx.baseline_sleep - fatigue_spike, 0.6))
                hrv = max(60.0, random.gauss(ctx.baseline_hrv - fatigue_spike * 5 + illness_factor * -3, 6))
                resting_hr = random.gauss(55 + fatigue_spike * 4 + illness_factor * 5, 3)
                fatigue = min(10.0, max(1.0, random.gauss(5 + fatigue_spike * 2 + illness_factor * 1.5, 1.2)))
                soreness = min(10.0, max(1.0, random.gauss(4 + fatigue_spike, 1.1)))
                mood = min(10.0, max(1.0, 8 - fatigue_spike * 1.5 - illness_factor * 1.2 + random.gauss(0, 0.5)))

                metrics = {
                    "SLEEP_HOURS": sleep,
                    "HRV": hrv,
                    "RESTING_HR": resting_hr,
                    "FATIGUE": fatigue,
                    "SORENESS": soreness,
                    "MOOD": mood,
                }

                for metric, value in metrics.items():
                    reading_id = uuid5(
                        NAMESPACE_DNS,
                        f"wellness-{ctx.athlete_id}-{metric}-{current_date.isoformat()}",
                    )
                    if await session.get(WellnessReading, reading_id):
                        continue

                    reading = WellnessReading(
                        id=reading_id,
                        tenant_id=org.id,
                        athlete_id=ctx.athlete_id,
                        source="SURVEY" if metric in {"FATIGUE", "SORENESS", "MOOD", "SLEEP_HOURS"} else "WEARABLE",
                        metric=metric,
                        value=round(float(value), 2),
                        unit="h" if metric == "SLEEP_HOURS" else "",
                        event_ts=datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc),
                    )
                    session.add(reading)

                daily_metrics[ctx.athlete_id].append(
                    {
                        "date": current_date,
                        "sleep": sleep,
                        "hrv": hrv,
                        "resting_hr": resting_hr,
                        "fatigue": fatigue,
                        "mood": mood,
                    }
                )

        # Post-processing features/predictions
        for ctx in athlete_contexts:
            records = sorted(daily_metrics[ctx.athlete_id], key=lambda x: x["date"])
            if not records:
                continue

            load_history = []
            hrv_history = []
            readiness_alerts = 0

            for rec in records:
                event_date = rec["date"]
                load_value = rec.get("load", 0.0)
                if load_value:
                    load_history.append((event_date, load_value))
                hrv_history.append((event_date, rec.get("hrv", ctx.baseline_hrv)))

                window_7 = [l for d, l in load_history if 0 <= (event_date - d).days <= 6]
                window_28 = [l for d, l in load_history if 0 <= (event_date - d).days <= 27]
                acute = sum(window_7)
                chronic = sum(window_28) / 4 if window_28 else 1.0
                acr = acute / chronic if chronic else 0

                hrv_vals = [v for d, v in hrv_history if 0 <= (event_date - d).days <= 27]
                hrv_baseline = float(np.mean(hrv_vals)) if hrv_vals else ctx.baseline_hrv
                sleep_window = [r.get("sleep", ctx.baseline_sleep) for r in records if 0 <= (event_date - r["date"]).days <= 6]
                sleep_debt = max(0.0, 8 * len(sleep_window) - sum(sleep_window))
                fatigue_window = [r.get("fatigue", 5.0) for r in records if 0 <= (event_date - r["date"]).days <= 6]
                fatigue_mean = float(np.mean(fatigue_window)) if fatigue_window else 5.0
                fatigue_std = float(np.std(fatigue_window)) if len(fatigue_window) > 1 else 1.0
                fatigue_z = (rec.get("fatigue", 5.0) - fatigue_mean) / (fatigue_std or 1.0)

                readiness = 100 - (acr * 15) - (sleep_debt * 2.5) - max(0, fatigue_z) * 10
                readiness = max(10, min(95, readiness))

                feature_timestamp = datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc)

                feature_rows = [
                    ("acute_chronic_ratio_7_28", round(acr, 3)),
                    ("rolling_hrv_baseline_28d", round(hrv_baseline, 2)),
                    ("sleep_debt_hours_7d", round(sleep_debt, 2)),
                    ("wellness_survey_z", round(fatigue_z, 3)),
                    ("readiness_score", round(readiness, 2)),
                ]

                for feature_name, value in feature_rows:
                    feature_pk = {
                        "tenant_id": org.id,
                        "athlete_id": ctx.athlete_id,
                        "feature_name": feature_name,
                        "event_ts": feature_timestamp,
                    }
                    existing_feature = await session.get(Feature, feature_pk)
                    if existing_feature:
                        existing_feature.feature_value = value
                    else:
                        session.add(
                            Feature(
                                feature_value=value,
                                **feature_pk,
                            )
                        )

                prediction_uuid = _prediction_id(org.id, ctx.athlete_id, event_date)
                severity = (
                    PredictionSeverity.CRITICAL
                    if readiness < 45
                    else PredictionSeverity.HIGH
                    if readiness < 55
                    else PredictionSeverity.MEDIUM
                    if readiness < 65
                    else PredictionSeverity.LOW
                )

                prediction = await session.get(Prediction, prediction_uuid)
                drivers = {
                    "acr_7_28": round(acr, 3),
                    "sleep_debt": round(sleep_debt, 2),
                    "fatigue_z": round(fatigue_z, 3),
                    "hrv_baseline": round(hrv_baseline, 2),
                }
                if prediction:
                    prediction.score = round(readiness, 2)
                    prediction.severity = severity
                    prediction.drivers = drivers
                else:
                    session.add(
                        Prediction(
                            id=prediction_uuid,
                            tenant_id=org.id,
                            athlete_id=ctx.athlete_id,
                            model_version=settings.ML_MODEL_VERSION,
                            score=round(readiness, 2),
                            severity=severity,
                            drivers=drivers,
                            event_ts=feature_timestamp,
                        )
                    )

                if severity in {PredictionSeverity.CRITICAL, PredictionSeverity.HIGH} and readiness_alerts < 6:
                    alert_uuid = _alert_id(org.id, ctx.athlete_id, event_date, "readiness_policy_v1")
                    alert = await session.get(Alert, alert_uuid)
                    if not alert:
                        session.add(
                            Alert(
                                id=alert_uuid,
                                tenant_id=org.id,
                                athlete_id=ctx.athlete_id,
                                session_id=None,
                                status=AlertStatus.OPEN,
                                severity=severity,
                                policy_id="readiness_policy_v1",
                                opened_at=feature_timestamp,
                            )
                        )
                        tenants_created_alerts += 1
                        readiness_alerts += 1

    if tenants_created_alerts < 12:
        print(f"⚠️ Tenant {org.slug} generated only {tenants_created_alerts} alerts (<12). Consider re-running with different seed.")


async def main() -> None:
    print("🚀 Seeding Sessions & Wellness demo data (Team B)")
    async with async_session_maker() as session:
        for tenant_cfg in TENANT_CONFIG:
            org = await ensure_organization(
                session,
                slug=tenant_cfg["slug"],
                name=tenant_cfg["name"],
                city=tenant_cfg["city"],
                country=tenant_cfg["country"],
            )
            await session.commit()

            await set_rls_context(
                session,
                tenant_id=str(org.id),
                user_role="OWNER",
                user_id=str(uuid4()),
            )
            print(f"➡️  Seeding tenant {tenant_cfg['slug']} ({tenant_cfg['name']})")
            await seed_tenant_data(session, org)
            await session.commit()

    print("✅ Sessions & Wellness seeding completed.")


if __name__ == "__main__":
    asyncio.run(main())


"""
Job for calculating player metrics: ACWR, Monotony, Strain, and Readiness Index.

This job runs nightly to update metrics for all players based on their training load and wellness data.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

logger = logging.getLogger(__name__)


# ============================================
# HELPER FUNCTIONS FOR METRIC CALCULATIONS
# ============================================

def calculate_acwr(load_7d: float, load_28d: float) -> Optional[float]:
    """
    Calculate Acute:Chronic Workload Ratio.

    ACWR = mean_7_days / mean_28_days

    Returns None if load_28d is 0 or insufficient data.
    """
    if load_28d == 0 or load_28d is None:
        return None
    return load_7d / load_28d


def calculate_monotony(loads_7d: List[float]) -> Optional[float]:
    """
    Calculate Monotony = mean / std for the last 7 days.

    Uses minimum std of 0.1 to avoid division by zero.
    Returns None if insufficient data.
    """
    if len(loads_7d) < 3:  # Need at least 3 days for meaningful std
        return None

    mean = np.mean(loads_7d)
    std = np.std(loads_7d, ddof=1)  # Sample std

    # Minimum std to avoid division by zero
    std = max(std, 0.1)

    return mean / std


def calculate_strain(total_load_7d: float, monotony: Optional[float]) -> Optional[float]:
    """
    Calculate Strain = total_load_7d × monotony.

    Returns None if monotony is None.
    """
    if monotony is None:
        return None
    return total_load_7d * monotony


def normalize_wellness_score(wellness_data: Dict) -> float:
    """
    Normalize wellness score to 0-1 range.

    Weighted average of:
    - Sleep quality (1-5) × 0.3
    - Fatigue (1-5, inverted) × 0.25
    - Stress (1-5, inverted) × 0.2
    - Mood (1-5) × 0.15
    - DOMS (1-5, inverted) × 0.1

    Lower fatigue/stress/DOMS = better, so we invert them.
    """
    sleep_q = wellness_data.get('sleep_quality', 3.0)
    fatigue = wellness_data.get('fatigue', 3.0)
    stress = wellness_data.get('stress', 3.0)
    mood = wellness_data.get('mood', 3.0)
    doms = wellness_data.get('doms', 3.0)

    # Normalize to 0-1 (5 is best for sleep/mood, 1 is best for fatigue/stress/doms)
    sleep_norm = (sleep_q - 1) / 4.0
    fatigue_norm = (5 - fatigue) / 4.0  # Inverted
    stress_norm = (5 - stress) / 4.0    # Inverted
    mood_norm = (mood - 1) / 4.0
    doms_norm = (5 - doms) / 4.0        # Inverted

    # Weighted average
    wellness_score = (
        0.30 * sleep_norm +
        0.25 * fatigue_norm +
        0.20 * stress_norm +
        0.15 * mood_norm +
        0.10 * doms_norm
    )

    return max(0.0, min(1.0, wellness_score))


def normalize_sleep_hours(sleep_hours: Optional[float]) -> float:
    """
    Normalize sleep hours to 0-1 range.

    8 hours = 1.0 (optimal)
    4 hours = 0.0
    12+ hours = 1.0 (capped)
    """
    if sleep_hours is None:
        return 0.5  # Default middle value if no data

    # Clamp between 4 and 12 hours
    sleep = max(4.0, min(12.0, sleep_hours))

    # Normalize: 8h = 1.0, 4h = 0.0
    if sleep <= 8:
        return (sleep - 4) / 4.0
    else:
        # Above 8h, still good but capped at 1.0
        return 1.0


def calculate_hrv_z_score(hrv: Optional[float], hrv_mean_28d: Optional[float], hrv_std_28d: Optional[float]) -> float:
    """
    Calculate HRV z-score relative to player's 28-day baseline.

    Higher HRV = better recovery.
    Returns 0.0 if insufficient data.
    """
    if hrv is None or hrv_mean_28d is None or hrv_std_28d is None or hrv_std_28d == 0:
        return 0.0

    z_score = (hrv - hrv_mean_28d) / hrv_std_28d

    # Clamp z-score to reasonable range (-3, +3) and normalize to 0-1
    z_score = max(-3.0, min(3.0, z_score))
    normalized = (z_score + 3) / 6.0  # -3 -> 0, 0 -> 0.5, +3 -> 1.0

    return normalized


def calculate_readiness(
    wellness_score_norm: float,
    hrv_z: float,
    acwr: Optional[float],
    sleep_norm: float
) -> float:
    """
    Calculate Readiness Index (0-100).

    Formula:
    readiness = 40% × wellness_score_norm +
                25% × hrv_z +
                25% × (1 - |acwr - 1|) +
                10% × sleep_norm

    Clamped to 0-100 range.
    """
    # ACWR component: optimal is 1.0, penalize deviation
    if acwr is not None:
        acwr_component = 1.0 - min(abs(acwr - 1.0), 1.0)  # Cap penalty at 1.0
    else:
        acwr_component = 0.5  # Neutral if no ACWR data

    readiness = (
        0.40 * wellness_score_norm +
        0.25 * hrv_z +
        0.25 * acwr_component +
        0.10 * sleep_norm
    )

    # Convert to 0-100 scale
    readiness_100 = readiness * 100

    return max(0.0, min(100.0, readiness_100))


# ============================================
# MAIN JOB FUNCTION
# ============================================

async def update_player_metrics():
    """
    Main job to calculate and update player metrics for all players.

    Runs nightly to update ACWR, Monotony, Strain, and Readiness.
    """
    logger.info("🔄 Starting player metrics calculation job...")

    async for session in get_session():
        try:
            # Get all active players
            players_result = await session.execute(
                text("SELECT id FROM players WHERE is_active = true")
            )
            players = players_result.fetchall()

            logger.info(f"Found {len(players)} active players")

            updated_count = 0

            for player_row in players:
                player_id = player_row[0]

                try:
                    # Calculate metrics for this player
                    await calculate_player_metrics(session, player_id)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error calculating metrics for player {player_id}: {e}", exc_info=True)
                    continue

            await session.commit()
            logger.info(f"✅ Metrics updated for {updated_count} players")

        except Exception as e:
            logger.error(f"Error in metrics calculation job: {e}", exc_info=True)
            await session.rollback()
        finally:
            await session.close()
            break  # Exit the generator loop


async def calculate_player_metrics(session: AsyncSession, player_id: UUID):
    """
    Calculate metrics for a single player for the last 35 days.

    Args:
        session: Database session
        player_id: Player UUID
    """
    today = date.today()
    start_date = today - timedelta(days=35)

    # ========================================
    # 1. FETCH TRAINING LOAD DATA
    # ========================================
    load_query = text("""
        SELECT
            ts.session_date::date as date,
            COALESCE(SUM(ps.session_load), 0) as daily_load
        FROM training_sessions ts
        LEFT JOIN player_session ps ON ps.session_id = ts.id AND ps.player_id = :player_id
        WHERE ts.session_date >= :start_date
        GROUP BY ts.session_date::date
        ORDER BY ts.session_date::date
    """)

    load_result = await session.execute(
        load_query,
        {"player_id": str(player_id), "start_date": start_date}
    )
    load_rows = load_result.fetchall()

    # Create date -> load map
    load_map = {row[0]: float(row[1]) for row in load_rows}

    # ========================================
    # 2. FETCH WELLNESS DATA
    # ========================================
    wellness_query = text("""
        SELECT
            date,
            sleep_hours,
            sleep_quality,
            fatigue_rating,
            stress_rating,
            mood_rating,
            doms_rating,
            hrv_ms
        FROM wellness_data
        WHERE player_id = :player_id
          AND date >= :start_date
        ORDER BY date
    """)

    wellness_result = await session.execute(
        wellness_query,
        {"player_id": str(player_id), "start_date": start_date}
    )
    wellness_rows = wellness_result.fetchall()

    # Create date -> wellness data map
    wellness_map = {}
    for row in wellness_rows:
        wellness_map[row[0]] = {
            'sleep_hours': row[1],
            'sleep_quality': row[2],
            'fatigue': row[3],
            'stress': row[4],
            'mood': row[5],
            'doms': row[6],
            'hrv': row[7]
        }

    # ========================================
    # 3. CALCULATE METRICS DAY BY DAY
    # ========================================
    for day_offset in range(35):
        current_date = start_date + timedelta(days=day_offset)

        # Get daily load
        daily_load = load_map.get(current_date, 0.0)

        # Get last 7 and 28 days of loads
        loads_7d = []
        loads_28d = []

        for i in range(1, 29):
            past_date = current_date - timedelta(days=i)
            past_load = load_map.get(past_date, 0.0)

            if i <= 7:
                loads_7d.append(past_load)
            loads_28d.append(past_load)

        # Calculate load averages
        load_7d_mean = np.mean(loads_7d) if loads_7d else 0.0
        load_28d_mean = np.mean(loads_28d) if loads_28d else 0.0

        # Calculate ACWR
        acwr = calculate_acwr(load_7d_mean, load_28d_mean)

        # Calculate Monotony
        monotony = calculate_monotony(loads_7d)

        # Calculate Strain
        total_load_7d = sum(loads_7d)
        strain = calculate_strain(total_load_7d, monotony)

        # ========================================
        # 4. CALCULATE READINESS
        # ========================================
        wellness_today = wellness_map.get(current_date)

        if wellness_today:
            # Wellness score
            wellness_score_norm = normalize_wellness_score(wellness_today)

            # Sleep
            sleep_norm = normalize_sleep_hours(wellness_today.get('sleep_hours'))

            # HRV z-score (need 28-day baseline)
            hrv_values_28d = []
            for i in range(1, 29):
                past_date = current_date - timedelta(days=i)
                past_wellness = wellness_map.get(past_date)
                if past_wellness and past_wellness.get('hrv'):
                    hrv_values_28d.append(past_wellness['hrv'])

            hrv_mean_28d = np.mean(hrv_values_28d) if hrv_values_28d else None
            hrv_std_28d = np.std(hrv_values_28d, ddof=1) if len(hrv_values_28d) > 1 else None
            hrv_today = wellness_today.get('hrv')

            hrv_z = calculate_hrv_z_score(hrv_today, hrv_mean_28d, hrv_std_28d)

            # Calculate Readiness
            readiness = calculate_readiness(wellness_score_norm, hrv_z, acwr, sleep_norm)
        else:
            readiness = None

        # ========================================
        # 5. UPSERT METRICS
        # ========================================
        upsert_query = text("""
            INSERT INTO player_metrics_daily (player_id, date, acwr, monotony, strain, readiness)
            VALUES (:player_id, :date, :acwr, :monotony, :strain, :readiness)
            ON CONFLICT (player_id, date)
            DO UPDATE SET
                acwr = EXCLUDED.acwr,
                monotony = EXCLUDED.monotony,
                strain = EXCLUDED.strain,
                readiness = EXCLUDED.readiness,
                created_at = now()
        """)

        await session.execute(
            upsert_query,
            {
                "player_id": str(player_id),
                "date": current_date,
                "acwr": acwr,
                "monotony": monotony,
                "strain": strain,
                "readiness": readiness
            }
        )

    logger.debug(f"Calculated metrics for player {player_id} for {35} days")

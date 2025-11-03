"""
Job for generating player alerts based on ACWR, Monotony, Strain, and Readiness thresholds.

This job runs daily after metrics calculation to identify risk conditions.
Automatically sends notifications through configured channels (email, telegram, webpush).
"""

import logging
from datetime import date
from typing import List, Optional, Tuple, Dict
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.notifications import send_notification

logger = logging.getLogger(__name__)


# ============================================
# ALERT THRESHOLDS AND RULES
# ============================================

ALERT_RULES = [
    # (metric, operator, threshold, level, message_template)
    ('acwr', '>', 1.5, 'warning', 'Rischio sovraccarico: ACWR > 1.5 (valore: {value:.2f})'),
    ('acwr', '<', 0.8, 'warning', 'Sotto-allenato: ACWR < 0.8 (valore: {value:.2f})'),
    ('monotony', '>', 2.0, 'warning', 'Carichi troppo ripetitivi: Monotonia > 2.0 (valore: {value:.2f})'),
    ('strain', '>', 2000, 'critical', 'Eccessivo stress cumulativo: Strain > 2000 (valore: {value:.0f})'),
    ('readiness', '<', 60, 'critical', 'Bassa prontezza fisica: Readiness < 60 (valore: {value:.0f})'),
    ('readiness', '>', 85, 'info', 'Ottimo stato di forma: Readiness > 85 (valore: {value:.0f})'),
]


async def get_custom_thresholds(session: AsyncSession, player_id: UUID) -> Dict:
    """
    Fetch custom alert thresholds for a player from alert_preferences table.

    Returns dict with structure: {metric: [(threshold_min, threshold_max, level), ...]}
    If no custom thresholds exist, returns empty dict (default rules will be used).
    """
    query = text("""
        SELECT metric, threshold_min, threshold_max, level
        FROM alert_preferences
        WHERE player_id = :player_id
        ORDER BY metric, level
    """)

    result = await session.execute(query, {"player_id": str(player_id)})
    rows = result.fetchall()

    custom_thresholds = {}
    for row in rows:
        metric = row[0].lower()
        threshold_min = float(row[1]) if row[1] is not None else None
        threshold_max = float(row[2]) if row[2] is not None else None
        level = row[3]

        if metric not in custom_thresholds:
            custom_thresholds[metric] = []
        custom_thresholds[metric].append((threshold_min, threshold_max, level))

    return custom_thresholds


async def get_notification_channels(session: AsyncSession, player_id: UUID) -> List[Dict]:
    """
    Fetch active notification channels for a player.

    Returns list of dicts with channel and address information.
    """
    query = text("""
        SELECT channel, address
        FROM alert_channels
        WHERE player_id = :player_id
          AND active = true
    """)

    result = await session.execute(query, {"player_id": str(player_id)})
    rows = result.fetchall()

    return [{"channel": row[0], "address": row[1]} for row in rows]


def evaluate_alert_conditions(metrics: dict) -> List[Tuple[str, str, str]]:
    """
    Evaluate metrics against alert rules.

    Args:
        metrics: Dictionary with keys 'acwr', 'monotony', 'strain', 'readiness'

    Returns:
        List of (alert_type, level, message) tuples for triggered alerts
    """
    triggered_alerts = []

    for metric_name, operator, threshold, level, message_template in ALERT_RULES:
        value = metrics.get(metric_name)

        if value is None:
            continue

        triggered = False
        if operator == '>' and value > threshold:
            triggered = True
        elif operator == '<' and value < threshold:
            triggered = True

        if triggered:
            alert_type = metric_name.upper()
            message = message_template.format(value=value)
            triggered_alerts.append((alert_type, level, message))

    return triggered_alerts


async def generate_alerts():
    """
    Main job to generate player alerts based on latest metrics.

    Runs daily to check all players' metrics and create/update alerts.
    """
    logger.info("🔄 Starting player alerts generation job...")

    async for session in get_session():
        try:
            today = date.today()

            # Get all active players with their latest metrics
            query = text("""
                SELECT
                    p.id as player_id,
                    p.first_name,
                    p.last_name,
                    pmd.date,
                    pmd.acwr,
                    pmd.monotony,
                    pmd.strain,
                    pmd.readiness
                FROM players p
                LEFT JOIN LATERAL (
                    SELECT *
                    FROM player_metrics_daily
                    WHERE player_id = p.id
                    ORDER BY date DESC
                    LIMIT 1
                ) pmd ON true
                WHERE p.is_active = true
            """)

            result = await session.execute(query)
            players = result.fetchall()

            logger.info(f"Found {len(players)} active players to check")

            alerts_created = 0
            alerts_resolved = 0

            for player_row in players:
                player_id = player_row[0]
                player_name = f"{player_row[1]} {player_row[2]}"
                metrics_date = player_row[3]

                if metrics_date is None:
                    logger.debug(f"No metrics found for player {player_name}")
                    continue

                # Build metrics dict
                metrics = {
                    'acwr': float(player_row[4]) if player_row[4] else None,
                    'monotony': float(player_row[5]) if player_row[5] else None,
                    'strain': float(player_row[6]) if player_row[6] else None,
                    'readiness': float(player_row[7]) if player_row[7] else None,
                }

                # Evaluate alert conditions
                triggered_alerts = evaluate_alert_conditions(metrics)

                # Get existing alerts for today
                existing_alerts_query = text("""
                    SELECT id, type, level, message, resolved
                    FROM player_alerts
                    WHERE player_id = :player_id AND date = :date
                """)

                existing_result = await session.execute(
                    existing_alerts_query,
                    {"player_id": str(player_id), "date": today}
                )
                existing_alerts = {row[1]: row for row in existing_result.fetchall()}

                # Process triggered alerts
                for alert_type, level, message in triggered_alerts:
                    if alert_type in existing_alerts:
                        # Alert already exists, ensure it's not resolved
                        existing = existing_alerts[alert_type]
                        if existing[4]:  # If resolved
                            # Reopen alert
                            update_query = text("""
                                UPDATE player_alerts
                                SET resolved = false
                                WHERE id = :id
                            """)
                            await session.execute(update_query, {"id": str(existing[0])})
                            logger.info(f"Reopened alert {alert_type} for {player_name}")
                    else:
                        # Create new alert
                        insert_query = text("""
                            INSERT INTO player_alerts (player_id, date, type, level, message, resolved)
                            VALUES (:player_id, :date, :type, :level, :message, false)
                            RETURNING id
                        """)
                        result = await session.execute(
                            insert_query,
                            {
                                "player_id": str(player_id),
                                "date": today,
                                "type": alert_type,
                                "level": level,
                                "message": message
                            }
                        )
                        alert_id = result.fetchone()[0]
                        alerts_created += 1
                        logger.info(f"Created {level} alert for {player_name}: {message}")

                        # Send notifications for new alerts
                        recipients = await get_notification_channels(session, player_id)
                        if recipients:
                            alert_data = {
                                "id": str(alert_id),
                                "player_id": str(player_id),
                                "player_name": player_name,
                                "type": alert_type,
                                "level": level,
                                "message": message,
                                "date": today.isoformat()
                            }
                            try:
                                notification_results = await send_notification(alert_data, recipients)
                                logger.info(f"Notifications sent for alert {alert_id}: {notification_results}")
                            except Exception as e:
                                logger.error(f"Failed to send notifications for alert {alert_id}: {e}")

                # Resolve alerts that are no longer triggered
                triggered_types = {a[0] for a in triggered_alerts}
                for alert_type, existing_data in existing_alerts.items():
                    if alert_type not in triggered_types and not existing_data[4]:
                        # Alert no longer triggered and not yet resolved
                        resolve_query = text("""
                            UPDATE player_alerts
                            SET resolved = true
                            WHERE id = :id
                        """)
                        await session.execute(resolve_query, {"id": str(existing_data[0])})
                        alerts_resolved += 1
                        logger.info(f"Resolved alert {alert_type} for {player_name}")

            await session.commit()
            logger.info(f"✅ Alerts generated: {alerts_created} new, {alerts_resolved} resolved")

        except Exception as e:
            logger.error(f"Error in alerts generation job: {e}", exc_info=True)
            await session.rollback()
        finally:
            await session.close()
            break  # Exit the generator loop

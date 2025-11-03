"""
Alerts API router for player risk alerts and notifications.

Endpoints for managing and viewing player alerts based on metrics thresholds.
"""

from datetime import date, datetime, timedelta
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.jobs.generate_alerts import generate_alerts
from app.schemas.alerts import PlayerAlert, PlayerAlertsList, TodayAlertsList
from app.schemas.preferences import (
    AlertPreference,
    AlertPreferenceCreate,
    PlayerPreferences,
    AlertChannel,
    AlertChannelCreate,
    AlertHistoryResponse,
    AlertHistoryItem
)
from app.notifications import send_notification

router = APIRouter()


@router.get("/player/{player_id}", response_model=PlayerAlertsList)
async def get_player_alerts(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(14, ge=1, le=90, description="Number of days to retrieve")
):
    """
    Get alerts for a specific player for the last N days.

    Returns list of alerts ordered by date descending (most recent first).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    query = text("""
        SELECT
            id,
            player_id,
            date,
            type,
            level,
            message,
            resolved,
            created_at
        FROM player_alerts
        WHERE player_id = :player_id
          AND date >= :start_date
          AND date <= :end_date
        ORDER BY date DESC, created_at DESC
    """)

    result = await session.execute(
        query,
        {
            "player_id": str(player_id),
            "start_date": start_date,
            "end_date": end_date
        }
    )
    rows = result.fetchall()

    alerts = [
        PlayerAlert(
            id=str(row[0]),
            player_id=str(row[1]),
            date=row[2],
            type=row[3],
            level=row[4],
            message=row[5],
            resolved=row[6],
            created_at=row[7]
        )
        for row in rows
    ]

    return PlayerAlertsList(
        player_id=player_id,
        alerts=alerts
    )


@router.get("/today", response_model=TodayAlertsList)
async def get_today_alerts(
    session: Annotated[AsyncSession, Depends(get_session)],
    resolved: bool = Query(False, description="Include resolved alerts")
):
    """
    Get all alerts for today across all players.

    Used by staff dashboard to see current risk situations.
    """
    today = date.today()

    resolved_condition = "" if resolved else "AND resolved = false"

    query = text(f"""
        SELECT
            pa.id,
            pa.player_id,
            pa.date,
            pa.type,
            pa.level,
            pa.message,
            pa.resolved,
            pa.created_at,
            p.first_name,
            p.last_name,
            p.jersey_number,
            p.role_primary
        FROM player_alerts pa
        JOIN players p ON p.id = pa.player_id
        WHERE pa.date = :today
          {resolved_condition}
        ORDER BY
            CASE pa.level
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                WHEN 'info' THEN 3
            END,
            p.last_name,
            p.first_name
    """)

    result = await session.execute(query, {"today": today})
    rows = result.fetchall()

    alerts = []
    for row in rows:
        alert_data = {
            "id": str(row[0]),
            "player_id": str(row[1]),
            "date": row[2],
            "type": row[3],
            "level": row[4],
            "message": row[5],
            "resolved": row[6],
            "created_at": row[7],
            "player_name": f"{row[8]} {row[9]}",
            "jersey_number": row[10],
            "role": row[11]
        }
        alerts.append(alert_data)

    return TodayAlertsList(
        date=today,
        alerts=alerts
    )


@router.patch("/{alert_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_alert(
    alert_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Mark an alert as resolved.

    This is typically done by staff after addressing the issue.
    """
    query = text("""
        UPDATE player_alerts
        SET resolved = true
        WHERE id = :alert_id
        RETURNING id
    """)

    result = await session.execute(query, {"alert_id": str(alert_id)})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    await session.commit()

    return {
        "status": "success",
        "message": f"Alert {alert_id} marked as resolved"
    }


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_alert_generation():
    """
    Manually trigger alert generation for all players.

    This endpoint is typically used by admins or for testing.
    In production, this runs automatically via scheduled job.
    """
    await generate_alerts()

    return {
        "status": "success",
        "message": "Alert generation triggered successfully"
    }


# ========== STEP 5: Alert Preferences & Notification Channels ==========

@router.get("/preferences/{player_id}", response_model=PlayerPreferences)
async def get_player_preferences(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Get alert preferences for a specific player.

    Returns custom thresholds if configured, otherwise returns defaults.
    Default thresholds: ACWR [0.8-1.5], MONOTONY [0-2.0], STRAIN [0-2500], READINESS [40-100]
    """
    query = text("""
        SELECT
            id,
            player_id,
            team_id,
            metric,
            threshold_min,
            threshold_max,
            level,
            updated_at
        FROM alert_preferences
        WHERE player_id = :player_id
        ORDER BY metric, level
    """)

    result = await session.execute(query, {"player_id": str(player_id)})
    rows = result.fetchall()

    preferences = [
        AlertPreference(
            id=row[0],
            player_id=row[1],
            team_id=row[2],
            metric=row[3],
            threshold_min=float(row[4]) if row[4] is not None else None,
            threshold_max=float(row[5]) if row[5] is not None else None,
            level=row[6],
            updated_at=row[7]
        )
        for row in rows
    ]

    return PlayerPreferences(
        player_id=player_id,
        preferences=preferences
    )


@router.post("/preferences/{player_id}", response_model=PlayerPreferences)
async def set_player_preferences(
    player_id: UUID,
    preferences: List[AlertPreferenceCreate],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Set or update alert preferences for a player.

    This will replace all existing preferences for the player.
    """
    # First, delete existing preferences for this player
    delete_query = text("""
        DELETE FROM alert_preferences
        WHERE player_id = :player_id
    """)
    await session.execute(delete_query, {"player_id": str(player_id)})

    # Insert new preferences
    insert_query = text("""
        INSERT INTO alert_preferences (player_id, metric, threshold_min, threshold_max, level)
        VALUES (:player_id, :metric, :threshold_min, :threshold_max, :level)
        RETURNING id, player_id, team_id, metric, threshold_min, threshold_max, level, updated_at
    """)

    inserted_preferences = []
    for pref in preferences:
        result = await session.execute(
            insert_query,
            {
                "player_id": str(player_id),
                "metric": pref.metric,
                "threshold_min": pref.threshold_min,
                "threshold_max": pref.threshold_max,
                "level": pref.level
            }
        )
        row = result.fetchone()
        inserted_preferences.append(
            AlertPreference(
                id=row[0],
                player_id=row[1],
                team_id=row[2],
                metric=row[3],
                threshold_min=float(row[4]) if row[4] is not None else None,
                threshold_max=float(row[5]) if row[5] is not None else None,
                level=row[6],
                updated_at=row[7]
            )
        )

    await session.commit()

    return PlayerPreferences(
        player_id=player_id,
        preferences=inserted_preferences
    )


@router.get("/history/{player_id}", response_model=AlertHistoryResponse)
async def get_alert_history(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    months: int = Query(6, ge=1, le=24, description="Number of months to retrieve")
):
    """
    Get monthly aggregated alert history for a player.

    Returns count of alerts by type and level for the last N months.
    Uses the vw_alerts_monthly view for efficient aggregation.
    """
    query = text(f"""
        SELECT
            month_start,
            type,
            level,
            count_alerts
        FROM vw_alerts_monthly
        WHERE player_id = :player_id
          AND month_start >= date_trunc('month', CURRENT_DATE - interval '{months} months')::date
        ORDER BY month_start DESC, type, level
    """)

    result = await session.execute(
        query,
        {"player_id": str(player_id)}
    )
    rows = result.fetchall()

    history = [
        AlertHistoryItem(
            month_start=row[0].isoformat(),
            type=row[1],
            level=row[2],
            count_alerts=row[3]
        )
        for row in rows
    ]

    return AlertHistoryResponse(
        player_id=player_id,
        months=months,
        history=history
    )


@router.post("/test-notification", status_code=status.HTTP_202_ACCEPTED)
async def send_test_notification(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    type: str = Query("ACWR", description="Alert type to test"),
    level: str = Query("warning", description="Alert level to test")
):
    """
    Send a test notification through all configured channels.

    Used by admins to test notification configuration (SMTP, Telegram, WebPush).
    """
    # Get player name
    player_query = text("""
        SELECT first_name, last_name
        FROM players
        WHERE id = :player_id
    """)
    player_result = await session.execute(player_query, {"player_id": str(player_id)})
    player_row = player_result.fetchone()

    if not player_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found"
        )

    player_name = f"{player_row[0]} {player_row[1]}"

    # Get configured notification channels for this player
    channels_query = text("""
        SELECT channel, address
        FROM alert_channels
        WHERE player_id = :player_id
          AND active = true
    """)
    channels_result = await session.execute(channels_query, {"player_id": str(player_id)})
    channels_rows = channels_result.fetchall()

    if not channels_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active notification channels configured for player {player_id}"
        )

    recipients = [
        {"channel": row[0], "address": row[1]}
        for row in channels_rows
    ]

    # Create mock alert
    mock_alert = {
        "id": "test-notification",
        "player_id": str(player_id),
        "player_name": player_name,
        "type": type,
        "level": level,
        "message": f"🧪 TEST NOTIFICATION: {type} {level} - This is a test notification to verify your alert channels are working correctly.",
        "date": date.today().isoformat()
    }

    # Send notification
    results = await send_notification(mock_alert, recipients)

    return {
        "status": "success",
        "message": f"Test notification sent to {len(recipients)} channel(s)",
        "player_name": player_name,
        "channels_tested": recipients,
        "results": results
    }


@router.get("/channels/{player_id}", response_model=List[AlertChannel])
async def get_player_channels(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Get all notification channels configured for a player.

    Returns list of channels (email, webpush, telegram) with their addresses and status.
    """
    query = text("""
        SELECT
            id,
            player_id,
            team_id,
            channel,
            address,
            active,
            created_at
        FROM alert_channels
        WHERE player_id = :player_id
        ORDER BY created_at DESC
    """)

    result = await session.execute(query, {"player_id": str(player_id)})
    rows = result.fetchall()

    channels = [
        AlertChannel(
            id=row[0],
            player_id=row[1],
            team_id=row[2],
            channel=row[3],
            address=row[4],
            active=row[5],
            created_at=row[6]
        )
        for row in rows
    ]

    return channels


@router.post("/channels/{player_id}", response_model=AlertChannel, status_code=status.HTTP_201_CREATED)
async def add_notification_channel(
    player_id: UUID,
    channel: AlertChannelCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Add a new notification channel for a player.

    Supports email, webpush, and telegram channels.
    """
    # Check if channel already exists for this player
    check_query = text("""
        SELECT id FROM alert_channels
        WHERE player_id = :player_id
          AND channel = :channel
          AND address = :address
    """)

    check_result = await session.execute(
        check_query,
        {
            "player_id": str(player_id),
            "channel": channel.channel,
            "address": channel.address
        }
    )

    if check_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel {channel.channel} with address {channel.address} already exists for this player"
        )

    # Insert new channel
    insert_query = text("""
        INSERT INTO alert_channels (player_id, channel, address, active)
        VALUES (:player_id, :channel, :address, :active)
        RETURNING id, player_id, team_id, channel, address, active, created_at
    """)

    result = await session.execute(
        insert_query,
        {
            "player_id": str(player_id),
            "channel": channel.channel,
            "address": channel.address,
            "active": channel.active
        }
    )
    row = result.fetchone()
    await session.commit()

    return AlertChannel(
        id=row[0],
        player_id=row[1],
        team_id=row[2],
        channel=row[3],
        address=row[4],
        active=row[5],
        created_at=row[6]
    )


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_channel(
    channel_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Delete a notification channel.

    This permanently removes the channel configuration.
    """
    query = text("""
        DELETE FROM alert_channels
        WHERE id = :channel_id
        RETURNING id
    """)

    result = await session.execute(query, {"channel_id": str(channel_id)})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    await session.commit()
    return None


@router.patch("/channels/{channel_id}/toggle", response_model=AlertChannel)
async def toggle_notification_channel(
    channel_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Toggle a notification channel active/inactive status.

    Allows enabling/disabling channels without deleting them.
    """
    query = text("""
        UPDATE alert_channels
        SET active = NOT active
        WHERE id = :channel_id
        RETURNING id, player_id, team_id, channel, address, active, created_at
    """)

    result = await session.execute(query, {"channel_id": str(channel_id)})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    await session.commit()

    return AlertChannel(
        id=row[0],
        player_id=row[1],
        team_id=row[2],
        channel=row[3],
        address=row[4],
        active=row[5],
        created_at=row[6]
    )


# ========== Web Push Subscriptions ==========

@router.post("/push/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_to_push(
    endpoint: str,
    p256dh: str,
    auth: str,
    user_id: Optional[UUID] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None
):
    """
    Register a Web Push subscription.

    Args:
        endpoint: Push service endpoint URL
        p256dh: Public key for encryption
        auth: Authentication secret
        user_id: Optional user ID (for multi-user support)

    Returns:
        Subscription ID
    """
    # Check if subscription already exists
    check_query = text("""
        SELECT id FROM push_subscriptions
        WHERE endpoint = :endpoint
    """)

    check_result = await session.execute(check_query, {"endpoint": endpoint})
    existing = check_result.fetchone()

    if existing:
        # Update existing subscription
        update_query = text("""
            UPDATE push_subscriptions
            SET p256dh = :p256dh,
                auth = :auth,
                active = true,
                user_id = :user_id
            WHERE endpoint = :endpoint
            RETURNING id
        """)

        result = await session.execute(
            update_query,
            {
                "endpoint": endpoint,
                "p256dh": p256dh,
                "auth": auth,
                "user_id": str(user_id) if user_id else None
            }
        )
        row = result.fetchone()
        await session.commit()

        return {"id": str(row[0]), "message": "Subscription updated"}

    # Create new subscription
    insert_query = text("""
        INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, active)
        VALUES (:user_id, :endpoint, :p256dh, :auth, true)
        RETURNING id
    """)

    result = await session.execute(
        insert_query,
        {
            "user_id": str(user_id) if user_id else None,
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth
        }
    )
    row = result.fetchone()
    await session.commit()

    return {"id": str(row[0]), "message": "Subscription created"}


@router.post("/push/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_push(
    endpoint: str,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Unregister a Web Push subscription.

    Args:
        endpoint: Push service endpoint URL to remove
    """
    query = text("""
        UPDATE push_subscriptions
        SET active = false
        WHERE endpoint = :endpoint
    """)

    await session.execute(query, {"endpoint": endpoint})
    await session.commit()

    return None

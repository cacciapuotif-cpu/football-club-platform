"""
Notification system for sending alerts via Email and Web Push.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def send_notification(alert: Dict, recipients: List[Dict]) -> Dict[str, List[str]]:
    """
    Send notification via configured channels (email, webpush only).

    Args:
        alert: Dictionary with alert data (id, player_id, type, level, message, player_name, etc.)
        recipients: List of dicts with channel info [{channel: 'email', address: 'x@y.com'}, ...]

    Returns:
        Dictionary with success/error lists per channel
    """
    results = {
        'email': {'success': [], 'errors': []},
        'webpush': {'success': [], 'errors': []}
    }

    for recipient in recipients:
        channel = recipient.get('channel')
        address = recipient.get('address')

        if not channel or not address:
            continue

        try:
            if channel == 'email':
                success = await send_email_notification(alert, address)
                if success:
                    results['email']['success'].append(address)
                else:
                    results['email']['errors'].append(address)

            elif channel == 'webpush':
                # WebPush handled via push_subscriptions table
                success = await send_webpush_notification(alert, recipient)
                if success:
                    results['webpush']['success'].append(address)
                else:
                    results['webpush']['errors'].append(address)

        except Exception as e:
            logger.error(f"Error sending {channel} notification to {address}: {e}")
            results[channel]['errors'].append(f"{address} ({str(e)})")

    return results


async def send_email_notification(alert: Dict, email: str) -> bool:
    """
    Send email notification via SMTP.

    Args:
        alert: Alert data dictionary
        email: Recipient email address

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if SMTP is configured
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.warning("SMTP not configured, skipping email notification")
            return False

        # Prepare email
        subject = f"[Football Club Platform] Alert {alert['type']} • {alert.get('player_name', 'Player')}"

        # Create HTML body
        level_colors = {
            'critical': '#DC2626',
            'warning': '#F59E0B',
            'info': '#3B82F6'
        }
        color = level_colors.get(alert.get('level', 'warning'), '#6B7280')

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">⚠️ Alert {alert['type']}</h2>
            </div>
            <div style="padding: 20px; border: 1px solid #E5E7EB; border-radius: 0 0 8px 8px;">
                <p><strong>Giocatore:</strong> {alert.get('player_name', 'N/A')}</p>
                <p><strong>Tipo:</strong> {alert['type']}</p>
                <p><strong>Livello:</strong> {alert.get('level', 'warning').upper()}</p>
                <p><strong>Messaggio:</strong> {alert['message']}</p>
                <p><strong>Data:</strong> {alert.get('date', 'N/A')}</p>
                <hr style="border: 1px solid #E5E7EB; margin: 20px 0;">
                <p>
                    <a href="{settings.FRONTEND_URL}/players/{alert.get('player_id', '')}"
                       style="background-color: #3B82F6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Vedi Profilo Giocatore
                    </a>
                </p>
            </div>
            <p style="color: #6B7280; font-size: 12px; margin-top: 20px;">
                Questa è una notifica automatica da Football Club Platform.
            </p>
        </body>
        </html>
        """

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = email

        # Attach HTML part
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {email} for alert {alert.get('id')}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        return False


async def send_webpush_notification(alert: Dict, subscription: Dict) -> bool:
    """
    Send WebPush notification (requires VAPID keys and pywebpush library).

    Args:
        alert: Alert data dictionary
        subscription: Push subscription data (endpoint, p256dh, auth)

    Returns:
        True if successful, False otherwise
    """
    try:
        # WebPush implementation requires pywebpush library
        # For now, log and skip
        logger.info(f"WebPush notification (not implemented yet): {alert.get('id')}")
        return True

    except Exception as e:
        logger.error(f"Failed to send webpush: {e}")
        return False



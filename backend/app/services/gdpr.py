"""
GDPR compliance services: data export, pseudonymization, right to erasure.
Production-ready privacy and data protection.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.player import Player
from app.models.user import User

logger = logging.getLogger(__name__)


class GDPRService:
    """GDPR compliance operations."""

    @staticmethod
    def pseudonymize_email(email: str) -> str:
        """Pseudonymize email address (one-way hash)."""
        hash_obj = hashlib.sha256(email.encode())
        return f"user_{hash_obj.hexdigest()[:16]}@pseudonymized.local"

    @staticmethod
    def pseudonymize_name(name: str) -> str:
        """Pseudonymize personal name."""
        hash_obj = hashlib.sha256(name.encode())
        return f"User_{hash_obj.hexdigest()[:8]}"

    @staticmethod
    async def export_user_data(session: AsyncSession, user_id: UUID) -> dict[str, Any]:
        """
        Export all personal data for a user (GDPR Article 15 - Right of Access).
        Returns structured JSON with all user data.
        """
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Basic user data
        data = {
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            },
            "exported_at": datetime.utcnow().isoformat(),
        }

        # If user is a player, include player data
        if user.player_id:
            player_result = await session.execute(select(Player).where(Player.id == user.player_id))
            player = player_result.scalar_one_or_none()
            if player:
                data["player"] = {
                    "first_name": player.first_name,
                    "last_name": player.last_name,
                    "date_of_birth": player.date_of_birth.isoformat(),
                    "email": player.email,
                    "phone": player.phone,
                    "consent_given": player.consent_given,
                    "consent_date": player.consent_date.isoformat() if player.consent_date else None,
                }

        # TODO: Add related data (sessions, wellness, injuries, etc.)

        logger.info(f"Data export completed for user {user_id}")
        return data

    @staticmethod
    async def anonymize_user(session: AsyncSession, user_id: UUID):
        """
        Anonymize user data (GDPR Article 17 - Right to Erasure).
        Pseudonymizes PII while keeping statistical data.
        """
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Pseudonymize user
        user.email = GDPRService.pseudonymize_email(user.email)
        user.full_name = GDPRService.pseudonymize_name(user.full_name)
        user.is_active = False

        # If linked player, pseudonymize
        if user.player_id:
            player_result = await session.execute(select(Player).where(Player.id == user.player_id))
            player = player_result.scalar_one_or_none()
            if player:
                player.first_name = "Anonymized"
                player.last_name = f"Player_{str(player.id)[:8]}"
                player.email = None
                player.phone = None
                player.address = None
                player.tax_code = None

        await session.commit()
        logger.info(f"User {user_id} anonymized")


# Singleton
gdpr_service = GDPRService()

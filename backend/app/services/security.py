"""
Security services: 2FA (TOTP), JWT refresh tokens, session management.
Production-ready authentication hardening.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import pyotp
import qrcode
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.user import User
from app.security import create_token

logger = logging.getLogger(__name__)


class TwoFactorAuth:
    """TOTP-based 2FA implementation."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, user_email: str) -> str:
        """Get TOTP provisioning URI for QR code."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=settings.APP_NAME,
        )

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify a TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 1 step window (30s before/after)

    @staticmethod
    def generate_qr_code(secret: str, user_email: str) -> BytesIO:
        """Generate QR code image for TOTP setup."""
        uri = TwoFactorAuth.get_totp_uri(secret, user_email)
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer


class RefreshTokenManager:
    """
    JWT refresh token management.
    Stores refresh tokens in-memory (use Redis for production scale).
    """

    # In production: use Redis with TTL
    _refresh_tokens: dict[str, dict] = {}

    @classmethod
    def create_refresh_token(cls, user_id: UUID) -> str:
        """Create a refresh token for user."""
        expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS)
        token = create_token({"sub": str(user_id), "type": "refresh"}, expires_delta=timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS))

        cls._refresh_tokens[token] = {
            "user_id": str(user_id),
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }
        return token

    @classmethod
    def verify_refresh_token(cls, token: str) -> Optional[str]:
        """Verify refresh token and return user_id if valid."""
        token_data = cls._refresh_tokens.get(token)
        if not token_data:
            return None

        if datetime.utcnow() > token_data["expires_at"]:
            cls.revoke_refresh_token(token)
            return None

        return token_data["user_id"]

    @classmethod
    def revoke_refresh_token(cls, token: str):
        """Revoke a refresh token (logout)."""
        cls._refresh_tokens.pop(token, None)

    @classmethod
    def revoke_user_tokens(cls, user_id: UUID):
        """Revoke all refresh tokens for a user."""
        user_id_str = str(user_id)
        tokens_to_revoke = [
            token for token, data in cls._refresh_tokens.items()
            if data["user_id"] == user_id_str
        ]
        for token in tokens_to_revoke:
            cls._refresh_tokens.pop(token)


# Singletons
two_factor_auth = TwoFactorAuth()
refresh_token_manager = RefreshTokenManager()

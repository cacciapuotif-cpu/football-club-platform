"""Authentication and security utilities."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.algorithms import RSAAlgorithm
from passlib.context import CryptContext

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token either via OIDC JWKS or shared secret."""
    if settings.OIDC_JWKS_URL:
        return _decode_oidc_token(token)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class _JWKSCache:
    """Simple in-memory JWKS cache with TTL."""

    def __init__(self) -> None:
        self._jwks: Dict[str, Any] = {}
        self._expires_at: float = 0.0

    def _refresh(self) -> None:
        if not settings.OIDC_JWKS_URL:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWKS URL not configured")

        response = httpx.get(settings.OIDC_JWKS_URL, timeout=settings.OIDC_HTTP_TIMEOUT)
        response.raise_for_status()
        self._jwks = response.json()
        self._expires_at = time.time() + settings.OIDC_JWKS_CACHE_SECONDS

    def get_key(self, kid: str) -> Dict[str, Any]:
        now = time.time()
        if now >= self._expires_at or not self._jwks:
            self._refresh()
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        # refresh once more in case key rotated recently
        self._refresh()
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise JWTError(f"Signing key not found for kid={kid}")


_jwks_cache = _JWKSCache()


def _decode_oidc_token(token: str) -> dict[str, Any]:
    try:
        unverified = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    kid = unverified.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing kid in token header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwk = _jwks_cache.get_key(kid)
    public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
    algorithms = [unverified.get("alg") or jwk.get("alg") or "RS256"]

    decode_kwargs: Dict[str, Any] = {
        "algorithms": algorithms,
    }
    if settings.OIDC_AUDIENCE:
        decode_kwargs["audience"] = settings.OIDC_AUDIENCE
    else:
        decode_kwargs["options"] = {"verify_aud": False}
    if settings.OIDC_ISSUER:
        decode_kwargs["issuer"] = settings.OIDC_ISSUER

    try:
        return jwt.decode(token, public_key, **decode_kwargs)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

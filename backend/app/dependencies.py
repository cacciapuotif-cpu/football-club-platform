"""FastAPI dependencies for authentication, tenancy, and RBAC."""

from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID, uuid4

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session, set_rls_context
from app.models.user import User, UserRole
from app.security import decode_token

security = HTTPBearer(auto_error=False)


ROLE_ALIAS_MAP = {
    "org_admin": UserRole.ADMIN,
    "coach": UserRole.COACH,
    "analyst": UserRole.ANALYST,
    "athlete": UserRole.PLAYER,
    "player": UserRole.PLAYER,
    "viewer": UserRole.VIEWER,
}


def _resolve_role(role_claim: Any) -> UserRole:
    if role_claim is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role claim missing")

    if isinstance(role_claim, (list, tuple)):
        for candidate in role_claim:
            mapped = ROLE_ALIAS_MAP.get(str(candidate).lower())
            if mapped:
                return mapped
        role_claim = role_claim[0]

    mapped = ROLE_ALIAS_MAP.get(str(role_claim).lower())
    if mapped:
        return mapped

    try:
        return UserRole(str(role_claim).upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unsupported role: {role_claim}",
        ) from exc


def _extract_claim(claims: dict[str, Any], key: str, *, required: bool = True) -> Optional[str]:
    value = claims.get(key)
    if value is None:
        if required:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Missing claim: {key}")
        return None
    if isinstance(value, (list, tuple)) and value:
        return str(value[0])
    return str(value)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Authenticate request and set session-level RLS context."""
    if settings.SKIP_AUTH:
        tenant_id = UUID("00000000-0000-0000-0000-0000000000aa")
        user_id = UUID("00000000-0000-0000-0000-0000000000ab")
        user = User(
            id=user_id,
            email="dev@localhost",
            hashed_password="",
            full_name="Dev User",
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=tenant_id,
        )
        await set_rls_context(
            session,
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            user_role=user.role.value,
        )
        setattr(user, "permissions", [])
        return user

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    claims = decode_token(credentials.credentials)
    tenant_claim = _extract_claim(claims, settings.OIDC_TENANT_CLAIM or "org_id")
    user_claim = _extract_claim(claims, settings.OIDC_USER_ID_CLAIM or "sub")
    email_claim = _extract_claim(claims, settings.OIDC_EMAIL_CLAIM or "email", required=False) or "user@unknown"
    role_claim = claims.get(settings.OIDC_ROLE_CLAIM or "roles")

    tenant_uuid = UUID(tenant_claim)
    user_uuid = UUID(user_claim) if user_claim else uuid4()
    resolved_role = _resolve_role(role_claim)

    result = await session.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=user_uuid,
            email=email_claim,
            hashed_password="",
            full_name=email_claim,
            role=resolved_role,
            is_active=True,
            organization_id=tenant_uuid,
        )

    await set_rls_context(
        session,
        tenant_id=str(tenant_uuid),
        user_id=str(user_uuid),
        user_role=resolved_role.value,
    )
    setattr(user, "permissions", [])
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_tenant_id(x_tenant_id: Annotated[str | None, Header()] = None) -> UUID | None:
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tenant-ID format") from exc
    return None


class RoleChecker:
    """Dependency to ensure the current user has one of the allowed roles."""

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in self.allowed_roles]}",
            )
        return current_user


require_owner = RoleChecker([UserRole.OWNER])
require_admin = RoleChecker([UserRole.OWNER, UserRole.ADMIN])
require_staff = RoleChecker(
    [
        UserRole.OWNER,
        UserRole.ADMIN,
        UserRole.COACH,
        UserRole.ANALYST,
        UserRole.MEDICAL,
        UserRole.PSYCHOLOGIST,
        UserRole.PHYSIO,
        UserRole.DOCTOR,
    ]
)
require_medical = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEDICAL, UserRole.PHYSIO, UserRole.DOCTOR])

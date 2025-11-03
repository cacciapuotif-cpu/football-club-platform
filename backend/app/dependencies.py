"""FastAPI dependencies for authentication, tenancy, and RBAC."""

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.user import User, UserRole
from app.security import decode_token

# Make security optional when SKIP_AUTH is enabled
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Get current authenticated user from JWT token.
    Raises 401 if token is invalid or user not found.
    Automatically sets RLS tenant_id for multi-tenant isolation.

    In development mode (SKIP_AUTH=true), returns a mock admin user.
    """
    # Skip authentication in development mode
    if os.getenv("SKIP_AUTH", "false").lower() == "true":
        # Get the first organization from the database for the mock user
        from app.models.organization import Organization
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()

        if not org:
            # Fallback to hardcoded org_id if no organization exists
            org_id = UUID("00000000-0000-0000-0000-000000000001")
        else:
            org_id = org.id

        # Return a mock admin user for development
        mock_user = User(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="dev@localhost",
            hashed_password="",
            role=UserRole.OWNER,
            is_active=True,
            organization_id=org_id,
        )
        # Set RLS tenant_id for Row Level Security
        from app.database import set_rls_tenant
        await set_rls_tenant(session, str(mock_user.organization_id))
        return mock_user

    # Normal authentication flow
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await session.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Set RLS tenant_id for Row Level Security
    from app.database import set_rls_tenant
    await set_rls_tenant(session, str(user.organization_id))

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user (alias for clarity)."""
    return current_user


def get_tenant_id(x_tenant_id: Annotated[str | None, Header()] = None) -> UUID | None:
    """
    Extract tenant ID from X-Tenant-ID header.
    Optional: defaults to user's organization_id if not provided.
    """
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tenant-ID format")
    return None


class RoleChecker:
    """
    Dependency to check if user has required role(s).
    Usage:
        @router.get("/admin", dependencies=[Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN]))])
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in self.allowed_roles]}",
            )
        return current_user


# Common role checkers
require_owner = RoleChecker([UserRole.OWNER])
require_admin = RoleChecker([UserRole.OWNER, UserRole.ADMIN])
require_staff = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.COACH, UserRole.ANALYST, UserRole.PHYSIO, UserRole.DOCTOR])
require_medical = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.PHYSIO, UserRole.DOCTOR])

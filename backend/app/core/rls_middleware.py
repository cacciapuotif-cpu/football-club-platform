"""
Row Level Security (RLS) Middleware
Automatic tenant isolation for all database queries.
"""

import logging
from typing import Callable, Optional

from fastapi import Request, Response
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import get_session

logger = logging.getLogger(__name__)


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sets PostgreSQL session variables for Row Level Security.

    This middleware automatically extracts tenant_id, user_id, and user_role
    from the request and sets them as PostgreSQL session variables, enabling
    automatic multi-tenant data isolation through RLS policies.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set RLS context before handling.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response: The HTTP response
        """
        # Extract tenant context from request
        tenant_id = self._extract_tenant_id(request)
        user_id = self._extract_user_id(request)
        user_role = self._extract_user_role(request)

        # Only set context if tenant_id is present
        if tenant_id:
            try:
                # Set RLS context for this request
                await self._set_rls_context(tenant_id, user_id, user_role)

                logger.debug(
                    f"RLS context set: tenant_id={tenant_id}, user_id={user_id}, role={user_role}"
                )

            except Exception as e:
                logger.error(f"Failed to set RLS context: {e}", exc_info=True)
                # Continue without RLS context - queries will return empty results
                # due to RLS policies blocking access

        # Process the request
        response = await call_next(request)

        # Clear RLS context after request (optional, as connections are pooled)
        # The context will be overwritten on the next request anyway
        if tenant_id:
            try:
                await self._clear_rls_context()
            except Exception as e:
                logger.warning(f"Failed to clear RLS context: {e}")

        return response

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant_id from request.

        Checks in order:
        1. Request state (set by auth middleware)
        2. X-Tenant-ID header
        3. Query parameter

        Args:
            request: The HTTP request

        Returns:
            Optional[str]: The tenant ID if found
        """
        # Check request state (set by auth middleware after JWT decode)
        if hasattr(request.state, "tenant_id"):
            return str(request.state.tenant_id)

        # Check custom header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # Check query parameter (useful for development)
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        return None

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user_id from request.

        Args:
            request: The HTTP request

        Returns:
            Optional[str]: The user ID if found
        """
        # Check request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return str(request.state.user_id)

        # Check custom header
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        return None

    def _extract_user_role(self, request: Request) -> Optional[str]:
        """
        Extract user_role from request.

        Args:
            request: The HTTP request

        Returns:
            Optional[str]: The user role if found
        """
        # Check request state (set by auth middleware)
        if hasattr(request.state, "user_role"):
            return str(request.state.user_role)

        # Check custom header
        user_role = request.headers.get("X-User-Role")
        if user_role:
            return user_role

        return None

    async def _set_rls_context(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> None:
        """
        Set PostgreSQL session variables for RLS.

        Args:
            tenant_id: The tenant/organization ID
            user_id: The user ID (optional)
            user_role: The user role (optional)
        """
        # Get database session
        async for session in get_session():
            try:
                # Set tenant_id (required)
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
                    {"tenant_id": tenant_id},
                )

                # Set user_id if provided
                if user_id:
                    await session.execute(
                        text("SELECT set_config('app.user_id', :user_id, false)"),
                        {"user_id": user_id},
                    )

                # Set user_role if provided
                if user_role:
                    await session.execute(
                        text("SELECT set_config('app.user_role', :user_role, false)"),
                        {"user_role": user_role},
                    )

                # Commit the settings
                await session.commit()

            finally:
                # Close the session
                await session.close()
            break

    async def _clear_rls_context(self) -> None:
        """
        Clear PostgreSQL session variables for RLS.
        """
        async for session in get_session():
            try:
                await session.execute(
                    text("""
                        SELECT set_config('app.tenant_id', '', false);
                        SELECT set_config('app.user_id', '', false);
                        SELECT set_config('app.user_role', '', false);
                    """)
                )
                await session.commit()
            except Exception as e:
                logger.warning(f"Error clearing RLS context: {e}")
            finally:
                await session.close()
            break


class RLSContextManager:
    """
    Context manager for manually setting RLS context.

    Use this for background jobs, CLI scripts, or any code that runs
    outside the request/response cycle.

    Example:
        async with RLSContextManager(tenant_id="org-123", user_id="user-456"):
            # All database queries in this block will use RLS context
            players = await session.execute(select(Player))
    """

    def __init__(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ):
        """
        Initialize RLS context manager.

        Args:
            tenant_id: The tenant/organization ID
            user_id: The user ID (optional)
            user_role: The user role (optional)
        """
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role
        self.session = None

    async def __aenter__(self):
        """Enter the context and set RLS variables."""
        async for session in get_session():
            self.session = session

            # Set tenant_id (required)
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
                {"tenant_id": self.tenant_id},
            )

            # Set user_id if provided
            if self.user_id:
                await session.execute(
                    text("SELECT set_config('app.user_id', :user_id, false)"),
                    {"user_id": self.user_id},
                )

            # Set user_role if provided
            if self.user_role:
                await session.execute(
                    text("SELECT set_config('app.user_role', :user_role, false)"),
                    {"user_role": self.user_role},
                )

            await session.commit()
            break

        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and clear RLS variables."""
        if self.session:
            try:
                await self.session.execute(
                    text("""
                        SELECT set_config('app.tenant_id', '', false);
                        SELECT set_config('app.user_id', '', false);
                        SELECT set_config('app.user_role', '', false);
                    """)
                )
                await self.session.commit()
            except Exception as e:
                logger.warning(f"Error clearing RLS context in context manager: {e}")
            finally:
                await self.session.close()


async def set_rls_context_for_session(
    session,
    tenant_id: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
) -> None:
    """
    Set RLS context for an existing database session.

    Use this when you already have a session and need to set RLS context.

    Args:
        session: SQLAlchemy async session
        tenant_id: The tenant/organization ID
        user_id: The user ID (optional)
        user_role: The user role (optional)
    """
    # Set tenant_id (required)
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
        {"tenant_id": tenant_id},
    )

    # Set user_id if provided
    if user_id:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, false)"),
            {"user_id": user_id},
        )

    # Set user_role if provided
    if user_role:
        await session.execute(
            text("SELECT set_config('app.user_role', :user_role, false)"),
            {"user_role": user_role},
        )

    await session.commit()


async def get_current_rls_context(session) -> dict:
    """
    Get current RLS context from database session.

    Args:
        session: SQLAlchemy async session

    Returns:
        dict: Current RLS context with tenant_id, user_id, and user_role
    """
    result = await session.execute(
        text("""
            SELECT
                current_setting('app.tenant_id', true) as tenant_id,
                current_setting('app.user_id', true) as user_id,
                current_setting('app.user_role', true) as user_role
        """)
    )
    row = result.fetchone()

    return {
        "tenant_id": row[0] if row else None,
        "user_id": row[1] if row else None,
        "user_role": row[2] if row else None,
    }

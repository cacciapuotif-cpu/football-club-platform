"""
Database configuration and session management.
Uses SQLModel with async support.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings

# Create async engine - force asyncpg driver
database_url = settings.DATABASE_URL
if "postgresql+asyncpg://" not in database_url:
    # Replace any postgresql variant with asyncpg
    database_url = database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False  # type: ignore
)


async def init_db() -> None:
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Use in FastAPI endpoints like:
        async def endpoint(session: AsyncSession = Depends(get_session))
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session (for use outside endpoints)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_rls_context(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str | None = None,
    user_role: str | None = None,
) -> None:
    """Set RLS context (tenant, user, role) for the current session."""
    from sqlalchemy import text

    await session.execute(text("SET app.tenant_id = :tenant_id"), {"tenant_id": tenant_id})
    if user_id:
        await session.execute(text("SET app.user_id = :user_id"), {"user_id": user_id})
    else:
        await session.execute(text("RESET app.user_id"))
    if user_role:
        await session.execute(text("SET app.user_role = :user_role"), {"user_role": user_role})
    else:
        await session.execute(text("RESET app.user_role"))


async def set_rls_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Backwards-compatible helper to set only tenant."""
    await set_rls_context(session, tenant_id=tenant_id)

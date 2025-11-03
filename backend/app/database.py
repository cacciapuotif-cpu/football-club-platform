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


async def set_rls_tenant(session: AsyncSession, tenant_id: str) -> None:
    """
    Set Row Level Security (RLS) tenant_id for current session.
    This enables Postgres RLS policies to filter data by tenant.

    Note: Uses raw SQL with f-string since asyncpg doesn't support
    parameterized SET commands. tenant_id is validated as UUID before this call.
    """
    from sqlalchemy import text
    # asyncpg doesn't support parameterized SET commands, so we use f-string
    # This is safe because tenant_id is validated as UUID in the caller
    await session.execute(text(f"SET app.tenant_id = '{tenant_id}'"))

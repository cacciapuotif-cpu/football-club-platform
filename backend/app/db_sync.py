"""
Synchronous database configuration for ML analytics and sync operations.
Uses standard SQLAlchemy with psycopg2.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from contextlib import contextmanager
from typing import Generator

from app.config import settings

# Create sync engine from DATABASE_URL
# Convert asyncpg URL to psycopg2 if needed
database_url_sync = settings.DATABASE_URL
if "postgresql+asyncpg://" in database_url_sync:
    database_url_sync = database_url_sync.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif "postgresql://" in database_url_sync and "psycopg2" not in database_url_sync:
    database_url_sync = database_url_sync.replace("postgresql://", "postgresql+psycopg2://")

engine_sync = create_engine(
    database_url_sync,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DB_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get synchronous database session for FastAPI.
    Usage:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for synchronous database session.
    Usage:
        with get_db_context() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

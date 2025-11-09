"""Alembic environment configuration."""

import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context

# --- PATH per importare app/*
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- Importa TUTTI i modelli (popola la metadata)
from app import models  # noqa: F401  # importa l'__init__ che carica tutti i model
from backend.app.config import settings

# Alembic Config object
config = context.config

# --- URL DB dalle tue settings (adatta alla tua funzione)
try:
    # Prefer a helper if available
    from app.database import get_engine_url  # type: ignore

    db_url = get_engine_url()  # sync str
except Exception:
    # Fallback alla URL diretta da settings
    db_url = settings.DATABASE_URL

# Override sqlalchemy.url from resolved URL
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # Ensure required extensions for UUID generation are present (for gen_random_uuid used by seeds)
    try:
        connection.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    except Exception:
        # Non-fatal in case of insufficient privileges; migrations can still run
        pass

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async support."""
    configuration = config.get_section(config.config_ini_section, {})
    # Force asyncpg driver for async migrations
    url = settings.DATABASE_URL
    if "postgresql+asyncpg://" not in url:
        url = url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

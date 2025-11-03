#!/usr/bin/env python3
"""
Direct table creation script using SQLModel.create_all()
This bypasses Alembic and creates all tables in the correct order.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlmodel import SQLModel

# Import all models to register them with SQLModel.metadata
from app.models import *  # noqa
from app.config import settings

# Use sync engine
database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
engine = create_engine(database_url, echo=True)

print("Creating all tables...")
SQLModel.metadata.create_all(engine)
print("✅ All tables created successfully!")

"""Create all database tables."""

import asyncio
from sqlmodel import SQLModel
from app.database import engine

# Import all models to register them with SQLModel
from app.models.user import User
from app.models.organization import Organization
from app.models.team import Team, Season
from app.models.player import Player
from app.models.match import Match, Attendance
from app.models.session import TrainingSession
from app.models.test import PhysicalTest, TechnicalTest, TacticalTest
from app.models.wellness import WellnessData
from app.models.injury import Injury
from app.models.performance import (
    TechnicalStats,
    TacticalCognitive,
    PsychologicalProfile,
    HealthMonitoring
)
from app.models.advanced_tracking import (
    PerformanceSnapshot,
    PlayerGoal,
    MatchPlayerStats,
    DailyReadiness,
    AutomatedInsight
)

async def create_tables():
    """Create all tables."""
    print("Creating all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())

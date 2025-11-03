"""
SQLModel database models.
All models are imported here for Alembic auto-generation.
"""

from app.models.audit import AuditLog
from app.models.benchmark import BenchmarkData
from app.models.injury import Injury
from app.models.match import Attendance, Match
from app.models.ml import DriftMetrics, MLModelVersion, MLPrediction
from app.models.organization import Organization
from app.models.performance import (
    HealthMonitoring,
    PsychologicalProfile,
    TacticalCognitive,
    TechnicalStats,
)
from app.models.plan import PlanAdherence, PlanTask, TrainingPlan
from app.models.player import Player
from app.models.player_stats import PlayerStats
from app.models.report import Report, ReportCache
from app.models.sensor import SensorData
from app.models.session import TrainingSession
from app.models.team import Season, Team
from app.models.test import PhysicalTest, TacticalTest, TechnicalTest, WellnessData
from app.models.user import User
from app.models.video import Video, VideoEvent
from app.models.advanced_tracking import (
    AutomatedInsight,
    DailyReadiness,
    MatchPlayerStats,
    PerformanceSnapshot,
    PlayerGoal,
)

__all__ = [
    "User",
    "Organization",
    "Team",
    "Season",
    "Player",
    "PlayerStats",
    "Match",
    "Attendance",
    "TrainingSession",
    "PhysicalTest",
    "TechnicalTest",
    "TacticalTest",
    "WellnessData",
    "TechnicalStats",
    "TacticalCognitive",
    "PsychologicalProfile",
    "HealthMonitoring",
    "Injury",
    "TrainingPlan",
    "PlanTask",
    "PlanAdherence",
    "Video",
    "VideoEvent",
    "SensorData",
    "MLPrediction",
    "MLModelVersion",
    "DriftMetrics",
    "Report",
    "ReportCache",
    "AuditLog",
    "BenchmarkData",
    # Advanced tracking models
    "PerformanceSnapshot",
    "PlayerGoal",
    "MatchPlayerStats",
    "DailyReadiness",
    "AutomatedInsight",
]

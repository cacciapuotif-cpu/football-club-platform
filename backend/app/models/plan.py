"""Training Plan models."""

from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class TrainingArea(str, Enum):
    """6 training areas."""

    TECHNICAL = "Tecnico"
    TACTICAL_COGNITIVE = "Tattico/Cognitivo"
    PHYSICAL = "Fisico"
    PSYCHOLOGICAL = "Psicologico/Mentale"
    LIFESTYLE_RECOVERY = "Lifestyle/Recupero"
    MEDICAL_PREVENTION = "Medico/Prevenzione"


class TaskStatus(str, Enum):
    """Task completion status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"


class TrainingPlan(SQLModel, table=True):
    """Weekly training plan for a player."""

    __tablename__ = "training_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Week
    week_start: date
    week_end: date
    is_active: bool = Field(default=True)

    # Target areas
    target_areas: list[str] = Field(default=[], sa_column=Column(JSON))

    # Generation metadata
    generated_by: str = Field(default="hybrid")  # hybrid, ml, rules
    model_version: str | None = None
    confidence: float | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class PlanTask(SQLModel, table=True):
    """Individual task (micro-objective) within a plan."""

    __tablename__ = "plan_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    plan_id: UUID = Field(foreign_key="training_plans.id", index=True)
    area: TrainingArea

    # Task details
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text))
    target_metric: str | None = None  # "km", "passing_accuracy", "sleep_hours"
    target_value: float | None = None
    target_unit: str | None = None

    # Scheduling
    scheduled_date: date | None = None
    priority: int = Field(default=3)  # 1-5

    # Status
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    completion_pct: float = Field(default=0.0)  # 0-100

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True


class PlanAdherence(SQLModel, table=True):
    """Adherence feedback for plan tasks."""

    __tablename__ = "plan_adherences"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="plan_tasks.id", index=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)

    # Adherence
    completed_date: date
    status: TaskStatus
    actual_value: float | None = None
    notes: str | None = Field(default=None, max_length=500)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True

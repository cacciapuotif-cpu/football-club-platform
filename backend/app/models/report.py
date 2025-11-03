"""Report and Report Cache models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class ReportType(str, Enum):
    """Report types."""

    PLAYER = "PLAYER"
    TEAM = "TEAM"
    STAFF_WEEKLY = "STAFF_WEEKLY"


class ReportFormat(str, Enum):
    """Report output formats."""

    PDF = "PDF"
    HTML = "HTML"
    JSON = "JSON"


class Report(SQLModel, table=True):
    """Generated report metadata."""

    __tablename__ = "reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    report_type: ReportType
    format: ReportFormat = Field(default=ReportFormat.PDF)

    # Subject
    player_id: UUID | None = Field(default=None, foreign_key="players.id", index=True)
    team_id: UUID | None = Field(default=None, foreign_key="teams.id", index=True)

    # Date range
    range_start: datetime
    range_end: datetime

    # Output
    storage_path: str = Field(max_length=1000)
    file_size_kb: float

    # Generation metadata
    generated_by: UUID | None = Field(default=None, foreign_key="users.id")  # User or system
    generation_duration_sec: float | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True


class ReportCache(SQLModel, table=True):
    """Cache for report generation."""

    __tablename__ = "report_caches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cache_key: str = Field(unique=True, max_length=255)
    report_id: UUID = Field(foreign_key="reports.id", index=True)

    # Expiry
    expires_at: datetime

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

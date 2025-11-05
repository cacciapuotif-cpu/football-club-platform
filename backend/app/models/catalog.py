"""
Metric catalog and data quality models.
Provides metadata for all metrics and tracks data quality issues.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel
from sqlalchemy import func


class MetricCatalog(SQLModel, table=True):
    """
    Catalog of all available metrics with metadata.
    Used for validation, unit conversion, and direction interpretation.
    """

    __tablename__ = "metric_catalog"

    metric_key: str = Field(primary_key=True, max_length=100)  # e.g., 'sleep_quality', 'hsr'

    # Metadata
    area: str | None = Field(default=None, max_length=50)  # wellness, training, match, physical_test
    description: str | None = Field(default=None, max_length=500)
    unit_default: str | None = Field(default=None, max_length=50)  # score, m, km, bpm, kg, etc.

    # Validation ranges
    min_value: float | None = Field(default=None, alias="min")
    max_value: float | None = Field(default=None, alias="max")

    # Interpretation
    direction: str | None = Field(default=None, max_length=50)  # up_is_better, down_is_better, neutral

    # Display
    display_name: str | None = Field(default=None, max_length=100)  # Human-readable name
    display_format: str | None = Field(default=None, max_length=50)  # decimal(1), integer, percentage

    # Status
    is_active: bool = Field(default=True)
    deprecated_at: datetime | None = Field(default=None)
    replacement_key: str | None = Field(default=None, max_length=100)  # if deprecated

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class DataQualityLog(SQLModel, table=True):
    """
    Log of data quality issues detected.
    Tracks validation failures, missing data, outliers, etc.
    """

    __tablename__ = "data_quality_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Entity reference (generic)
    entity_type: str = Field(max_length=100, alias="entity")  # wellness_metric, training_metric, match_metric
    entity_id: UUID  # ID of the problematic entity

    # Issue details
    issue_type: str = Field(max_length=100, alias="issue")  # out_of_range, missing_data, duplicate, outlier
    issue_details: str | None = Field(default=None, max_length=500)  # additional context

    # Severity
    severity: str = Field(default="warning", max_length=20)  # info, warning, error, critical

    # Resolution
    resolved: bool = Field(default=False)
    resolved_at: datetime | None = Field(default=None)
    resolution_note: str | None = Field(default=None, max_length=500)

    # Timestamps
    detected_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class DataCompleteness(SQLModel, table=True):
    """
    Tracks data completeness for players over time.
    Daily rollup for quick dashboard queries.
    """

    __tablename__ = "data_completeness"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    date: datetime = Field(index=True)

    # Completeness metrics (0-100%)
    wellness_completeness: float = Field(default=0, ge=0, le=100)
    training_completeness: float = Field(default=0, ge=0, le=100)
    match_completeness: float = Field(default=0, ge=0, le=100)

    # Counts
    wellness_metrics_count: int = Field(default=0, ge=0)
    training_sessions_count: int = Field(default=0, ge=0)
    matches_count: int = Field(default=0, ge=0)

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

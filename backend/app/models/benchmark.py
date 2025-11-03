"""Benchmark data model for anonymous role/age comparisons."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class BenchmarkData(SQLModel, table=True):
    """
    Anonymous benchmark data for role/age comparisons.
    Aggregated from opt-in organizations.
    """

    __tablename__ = "benchmark_data"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Demographics (anonymized)
    role: str = Field(max_length=10, index=True)  # GK, DF, MF, FW
    age_group: str = Field(max_length=10, index=True)  # U15, U17, U19, Pro

    # Time period
    period_start: datetime
    period_end: datetime

    # Sample size
    sample_count: int

    # Metrics (P25, P50, P75)
    metrics: dict = Field(sa_column=Column(JSON))
    # Example structure:
    # {
    #   "distance_km": {"p25": 8.2, "p50": 9.5, "p75": 10.8},
    #   "sprint_count": {"p25": 12, "p50": 18, "p75": 24},
    #   ...
    # }

    # Metadata
    data_version: int = Field(default=1)
    contributing_orgs: int  # Number of orgs (anonymized)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

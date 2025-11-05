"""
Match metrics with EAV structure.
Extends existing Match/Attendance models with flexible per-player metrics.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.match import Attendance


class MatchMetric(SQLModel, table=True):
    """
    Individual match metric for a player's performance.
    EAV structure for flexible GPS/physical/tactical data.

    Standard metric_keys:
    - sprint_count (#)
    - hsr (m) - High Speed Running
    - total_distance (km)
    - pass_accuracy (%)
    - pass_completed (#)
    - pass_attempted (#)
    - duels_won (#)
    - duels_total (#)
    - touches (#)
    - dribbles_success (#)
    - interceptions (#)
    - tackles (#)
    - shots_on_target (#)
    - shots_total (#)
    - avg_hr (bpm)
    - max_hr (bpm)
    - top_speed (km/h)
    - player_load (AU)
    """

    __tablename__ = "match_metrics"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    attendance_id: UUID = Field(foreign_key="attendances.id", index=True)

    # EAV structure
    metric_key: str = Field(index=True, max_length=100)
    metric_value: float
    unit: str | None = Field(default=None, max_length=50)  # 'm', 'km', 'bpm', '#', '%', 'score', 'AU'

    # Data quality
    validity: str = Field(default="valid", max_length=20)  # valid, invalid, suspect
    tags: str | None = Field(default=None, max_length=200)  # source, device_id, etc.

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class MatchPlayerPosition(SQLModel, table=True):
    """
    Player position/role during a match.
    Can have multiple positions if substitution or tactical change.
    """

    __tablename__ = "match_player_positions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    attendance_id: UUID = Field(foreign_key="attendances.id", index=True)

    position: str = Field(max_length=20)  # GK, DF, MF, FW, or specific (LW, RCB, etc.)
    minute_start: int = Field(default=0, ge=0, le=120)
    minute_end: int | None = Field(default=None, ge=0, le=120)

    # Tactical info
    formation_position: str | None = Field(default=None, max_length=50)  # 4-3-3 LW, 3-5-2 RWB

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

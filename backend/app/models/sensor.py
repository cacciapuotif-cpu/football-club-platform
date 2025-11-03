"""Sensor data model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class SensorData(SQLModel, table=True):
    """
    Generic sensor data model.
    Supports GPS, IMU, BLE, heart rate monitors.
    """

    __tablename__ = "sensor_data"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", index=True)
    session_id: UUID | None = Field(default=None, foreign_key="training_sessions.id", index=True)
    match_id: UUID | None = Field(default=None, foreign_key="matches.id", index=True)

    # Timestamp
    timestamp: datetime
    duration_sec: int | None = None

    # External loads (GPS)
    distance_m: float | None = None
    distance_km: float | None = None
    hi_runs: int | None = None  # High-intensity runs
    sprint_count: int | None = None
    top_speed_km_h: float | None = None
    accelerations: int | None = None
    decelerations: int | None = None
    player_load: float | None = None

    # Internal loads (HR)
    hr_avg_bpm: int | None = None
    hr_peak_bpm: int | None = None
    time_zone_1_sec: int | None = None  # <60% max HR
    time_zone_2_sec: int | None = None  # 60-70%
    time_zone_3_sec: int | None = None  # 70-80%
    time_zone_4_sec: int | None = None  # 80-90%
    time_zone_5_sec: int | None = None  # >90%

    # Raw data (optional, for advanced processing)
    raw_data: dict | None = Field(default=None, sa_column=Column(JSON))

    # Source
    data_source: str | None = Field(default=None, max_length=100)  # Catapult, STATSports, Polar

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

"""Video and Video Event models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    pass


class VideoStatus(str, Enum):
    """Video processing status."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventType(str, Enum):
    """Video event types."""

    SHOT = "SHOT"
    PASS = "PASS"
    CROSS = "CROSS"
    DRIBBLE = "DRIBBLE"
    TACKLE = "TACKLE"
    INTERCEPTION = "INTERCEPTION"
    CLEARANCE = "CLEARANCE"
    GOAL = "GOAL"
    ASSIST = "ASSIST"
    FOUL = "FOUL"
    OFFSIDE = "OFFSIDE"
    CORNER = "CORNER"
    FREE_KICK = "FREE_KICK"
    THROW_IN = "THROW_IN"


class Video(SQLModel, table=True):
    """Video asset with processing metadata."""

    __tablename__ = "videos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source
    filename: str = Field(max_length=500)
    original_url: str | None = Field(default=None, max_length=1000)
    storage_path: str = Field(max_length=1000)
    file_size_mb: float

    # Association
    match_id: UUID | None = Field(default=None, foreign_key="matches.id", index=True)
    session_id: UUID | None = Field(default=None, foreign_key="training_sessions.id", index=True)

    # Processing
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    error_message: str | None = Field(default=None, sa_column=Column(Text))

    # Video metadata
    duration_sec: float | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None

    # Processing results
    keyframes_path: str | None = None
    pose_data_path: str | None = None
    heatmap_path: str | None = None
    events_path: str | None = None

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True


class VideoEvent(SQLModel, table=True):
    """Detected event in video."""

    __tablename__ = "video_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    player_id: UUID | None = Field(default=None, foreign_key="players.id", index=True)

    # Event
    timestamp_sec: float
    event_type: EventType
    confidence: float  # 0-1

    # Location (normalized 0-1)
    x: float | None = None
    y: float | None = None

    # Metadata
    event_metadata: dict = Field(default={}, sa_column=Column(JSON))

    # Multi-tenancy
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    class Config:
        use_enum_values = True

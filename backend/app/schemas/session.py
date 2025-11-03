"""Training session schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.session import SessionType


class TrainingSessionBase(BaseModel):
    """Base training session fields."""

    session_date: datetime
    session_type: SessionType = SessionType.TRAINING
    duration_min: int = Field(..., ge=1, le=480)
    team_id: UUID
    focus: str | None = Field(default=None, max_length=255)
    description: str | None = None
    planned_intensity: int | None = Field(default=None, ge=1, le=10)
    actual_intensity_avg: float | None = None
    video_id: UUID | None = None


class TrainingSessionCreate(TrainingSessionBase):
    """Schema for creating a new training session."""
    pass


class TrainingSessionUpdate(BaseModel):
    """Schema for updating a training session."""

    session_date: Optional[datetime] = None
    session_type: Optional[SessionType] = None
    duration_min: Optional[int] = Field(default=None, ge=1, le=480)
    team_id: Optional[UUID] = None
    focus: Optional[str] = None
    description: Optional[str] = None
    planned_intensity: Optional[int] = None
    actual_intensity_avg: Optional[float] = None
    video_id: Optional[UUID] = None


class TrainingSessionResponse(TrainingSessionBase):
    """Schema for training session response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

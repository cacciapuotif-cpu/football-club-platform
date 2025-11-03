"""Training schemas for RPE tracking and session load calculation."""

from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RpeUpsertPayload(BaseModel):
    """Payload for upserting RPE data for a player session."""
    player_id: UUID
    session_id: UUID
    rpe: Decimal = Field(..., ge=0, le=10, decimal_places=1)

    @field_validator('rpe')
    @classmethod
    def validate_rpe(cls, v: Decimal) -> Decimal:
        """Ensure RPE is between 0 and 10 with max 1 decimal place."""
        if v < 0 or v > 10:
            raise ValueError('RPE must be between 0 and 10')
        return v


class RpeUpsertResponse(BaseModel):
    """Response after upserting RPE data."""
    player_id: UUID
    session_id: UUID
    rpe: Decimal
    duration_min: int
    session_load: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True


class WeeklyLoadPoint(BaseModel):
    """Single week data point for weekly load chart."""
    week_start: date
    weekly_load: Decimal

    class Config:
        from_attributes = True


class WeeklyLoadResponse(BaseModel):
    """Response containing weekly load aggregations for a player."""
    player_id: UUID
    weeks: List[WeeklyLoadPoint]
    total_current_week: Decimal

    class Config:
        from_attributes = True

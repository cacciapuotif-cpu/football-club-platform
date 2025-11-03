"""Wellness data schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WellnessDataBase(BaseModel):
    """Base wellness data fields."""

    date: date
    player_id: UUID

    # Sleep
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)

    # Recovery
    hrv_ms: float | None = Field(default=None, ge=0)
    resting_hr_bpm: int | None = Field(default=None, ge=30, le=220)
    doms_rating: int | None = Field(default=None, ge=1, le=5)

    # Perceived state
    fatigue_rating: int | None = Field(default=None, ge=1, le=5)
    stress_rating: int | None = Field(default=None, ge=1, le=5)
    mood_rating: int | None = Field(default=None, ge=1, le=5)
    motivation_rating: int | None = Field(default=None, ge=1, le=5)

    # Hydration
    hydration_rating: int | None = Field(default=None, ge=1, le=5)

    # Session RPE
    srpe: int | None = Field(default=None, ge=1, le=10)
    session_duration_min: int | None = Field(default=None, ge=0)
    training_load: float | None = Field(default=None, ge=0)

    notes: str | None = Field(default=None, max_length=500)


class WellnessDataCreate(WellnessDataBase):
    """Schema for creating wellness data."""
    pass


class WellnessDataUpdate(BaseModel):
    """Schema for updating wellness data."""

    date: Optional[date] = None
    player_id: Optional[UUID] = None
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    hrv_ms: Optional[float] = None
    resting_hr_bpm: Optional[int] = None
    doms_rating: Optional[int] = None
    fatigue_rating: Optional[int] = None
    stress_rating: Optional[int] = None
    mood_rating: Optional[int] = None
    motivation_rating: Optional[int] = None
    hydration_rating: Optional[int] = None
    srpe: Optional[int] = None
    session_duration_min: Optional[int] = None
    training_load: Optional[float] = None
    notes: Optional[str] = None


class WellnessDataResponse(WellnessDataBase):
    """Schema for wellness data response."""

    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# === NEW SCHEMAS FOR WELLNESS SUMMARY TABLE ===


class WellnessSummary(BaseModel):
    """Schema for wellness summary table - aggregated player wellness stats."""

    player_id: UUID
    cognome: str
    nome: str
    ruolo: str
    wellness_sessions_count: int
    last_entry_date: date | None

    class Config:
        from_attributes = True


class WellnessEntry(BaseModel):
    """Schema for individual wellness entry detail view."""

    date: date
    sleep_h: float | None
    sleep_quality: int | None
    fatigue: int | None
    stress: int | None
    mood: int | None
    doms: int | None
    weight_kg: float | None
    notes: str | None

    class Config:
        from_attributes = True

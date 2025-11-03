"""Player schemas for API request/response validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.player import DominantArm, DominantFoot, PlayerRole


class PlayerBase(BaseModel):
    """Base player fields."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    place_of_birth: str | None = Field(default=None, max_length=255)
    nationality: str = Field(default="IT", max_length=2)
    tax_code: str | None = Field(default=None, max_length=50)

    # Contact
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)

    # Guardian (for minors)
    is_minor: bool = False
    guardian_name: str | None = Field(default=None, max_length=255)
    guardian_email: str | None = Field(default=None, max_length=255)
    guardian_phone: str | None = Field(default=None, max_length=50)

    # Technical
    role_primary: PlayerRole
    role_secondary: PlayerRole | None = None
    dominant_foot: DominantFoot = DominantFoot.RIGHT
    dominant_arm: DominantArm = DominantArm.RIGHT
    jersey_number: int | None = None

    # Physical
    height_cm: float | None = None
    weight_kg: float | None = None
    bmi: float | None = None
    body_fat_pct: float | None = None
    lean_mass_kg: float | None = None

    # GDPR & Consent
    consent_given: bool = False
    consent_date: datetime | None = None
    consent_parent_given: bool | None = None
    data_retention_until: date | None = None

    # Status
    is_active: bool = True
    is_injured: bool = False
    notes: str | None = None

    # Team
    team_id: UUID | None = None


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    pass


class PlayerUpdate(BaseModel):
    """Schema for updating a player (all fields optional)."""

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    tax_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_minor: Optional[bool] = None
    guardian_name: Optional[str] = None
    guardian_email: Optional[str] = None
    guardian_phone: Optional[str] = None
    role_primary: Optional[PlayerRole] = None
    role_secondary: Optional[PlayerRole] = None
    dominant_foot: Optional[DominantFoot] = None
    dominant_arm: Optional[DominantArm] = None
    jersey_number: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    body_fat_pct: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    consent_given: Optional[bool] = None
    consent_date: Optional[datetime] = None
    consent_parent_given: Optional[bool] = None
    data_retention_until: Optional[date] = None
    is_active: Optional[bool] = None
    is_injured: Optional[bool] = None
    notes: Optional[str] = None
    team_id: Optional[UUID] = None


class PlayerResponse(PlayerBase):
    """Schema for player response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

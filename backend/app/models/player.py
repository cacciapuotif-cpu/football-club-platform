"""Player model with comprehensive profile."""

from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, Text
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.player_stats import PlayerStats
    from app.models.player_training_stats import PlayerTrainingStats
    from app.models.analytics import PlayerMatchStat, PlayerTrainingLoad, PlayerFeatureDaily, PlayerPrediction


class PlayerRole(str, Enum):
    """Player position roles."""

    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class DominantFoot(str, Enum):
    """Dominant foot."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


class DominantArm(str, Enum):
    """Dominant arm (for throw-ins, GK)."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Player(SQLModel, table=True):
    """
    Player model with complete profile.
    Includes: anagraphic, physical, medical, consent.
    """

    __tablename__ = "players"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # External ID for integration with other systems (optional, but recommended for idempotent seeding)
    external_id: str | None = Field(default=None, max_length=255, unique=True, index=True)

    # Anagraphic
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: date
    place_of_birth: str | None = Field(default=None, max_length=255)
    nationality: str = Field(default="IT", max_length=2)
    tax_code: str | None = Field(default=None, max_length=50)  # Codice fiscale

    # Contact
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)

    # Guardian (for minors)
    is_minor: bool = Field(default=False)
    guardian_name: str | None = Field(default=None, max_length=255)
    guardian_email: str | None = Field(default=None, max_length=255)
    guardian_phone: str | None = Field(default=None, max_length=50)

    # Technical
    role_primary: PlayerRole
    role_secondary: PlayerRole | None = Field(default=None)
    dominant_foot: DominantFoot = Field(default=DominantFoot.RIGHT)
    dominant_arm: DominantArm = Field(default=DominantArm.RIGHT)
    jersey_number: int | None = Field(default=None)

    # Physical (latest measurements)
    height_cm: float | None = Field(default=None)
    weight_kg: float | None = Field(default=None)
    bmi: float | None = Field(default=None)
    body_fat_pct: float | None = Field(default=None)
    lean_mass_kg: float | None = Field(default=None)

    # Physical condition & injury
    physical_condition: str | None = Field(default="normal", max_length=50)  # excellent, good, normal, poor
    injury_prone: bool = Field(default=False)

    # ============================================
    # TACTICAL ATTRIBUTES (1-100)
    # ============================================
    tactical_awareness: int = Field(default=50, ge=0, le=100)
    positioning: int = Field(default=50, ge=0, le=100)
    decision_making: int = Field(default=50, ge=0, le=100)
    work_rate: int = Field(default=50, ge=0, le=100)

    # ============================================
    # PSYCHOLOGICAL ATTRIBUTES (1-100)
    # ============================================
    mental_strength: int = Field(default=50, ge=0, le=100)
    leadership: int = Field(default=50, ge=0, le=100)
    concentration: int = Field(default=50, ge=0, le=100)
    adaptability: int = Field(default=50, ge=0, le=100)

    # Market & Contract
    market_value_eur: float | None = Field(default=None, ge=0)
    contract_expiry_date: date | None = Field(default=None)

    # GDPR & Consent
    consent_given: bool = Field(default=False)
    consent_date: datetime | None = Field(default=None)
    consent_parent_given: bool | None = Field(default=None)  # For minors
    data_retention_until: date | None = Field(default=None)

    # Medical clearance
    medical_clearance: bool = Field(default=False)
    medical_clearance_expiry: date | None = Field(default=None)

    # ML Computed Metrics
    overall_rating: float | None = Field(default=6.0, ge=0, le=10)
    potential_rating: float | None = Field(default=6.0, ge=0, le=10)
    form_level: float | None = Field(default=5.0, ge=0, le=10)

    # Profile photo
    foto_url: str | None = Field(default=None, max_length=500, description="URL foto profilo")

    # Status
    is_active: bool = Field(default=True)
    is_injured: bool = Field(default=False)
    notes: str | None = Field(default=None, sa_column=Column(Text))

    # Multi-tenancy & Team
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    team_id: UUID | None = Field(default=None, foreign_key="teams.id", index=True)
    team: Optional["Team"] = Relationship(back_populates="players")

    # Relationships
    player_stats: list["PlayerStats"] = Relationship(back_populates="player")
    training_stats: list["PlayerTrainingStats"] = Relationship(back_populates="player")

    # ML Analytics relationships - COMMENTED OUT to fix mapper initialization errors
    # TODO: Re-enable when analytics models are properly imported/defined
    # ml_match_stats: list["PlayerMatchStat"] = Relationship(back_populates="player")
    # ml_training_loads: list["PlayerTrainingLoad"] = Relationship(back_populates="player")
    # ml_features_daily: list["PlayerFeatureDaily"] = Relationship(back_populates="player")
    # ml_predictions: list["PlayerPrediction"] = Relationship(back_populates="player")

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    class Config:
        use_enum_values = True

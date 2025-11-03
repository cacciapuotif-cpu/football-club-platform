"""Player session models for RPE tracking and session load calculation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class PlayerSession(SQLModel, table=True):
    """
    Player session model for tracking RPE (Rate of Perceived Exertion) and session load.

    Session load is calculated as: rpe × duration_min
    """
    __tablename__ = "player_session"

    player_id: UUID = Field(foreign_key="players.id", primary_key=True)
    session_id: UUID = Field(foreign_key="training_sessions.id", primary_key=True)
    rpe: Optional[Decimal] = Field(default=None)
    session_load: Optional[Decimal] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

"""Schemas for player alerts."""

from datetime import date, datetime
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel


class PlayerAlert(BaseModel):
    """Individual player alert."""
    id: str
    player_id: str
    date: date
    type: str
    level: Literal['info', 'warning', 'critical']
    message: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PlayerAlertsList(BaseModel):
    """List of alerts for a player."""
    player_id: UUID
    alerts: List[PlayerAlert]

    class Config:
        from_attributes = True


class TodayAlertsList(BaseModel):
    """List of all today's alerts across all players."""
    date: date
    alerts: List[dict]  # Contains player info + alert data

    class Config:
        from_attributes = True

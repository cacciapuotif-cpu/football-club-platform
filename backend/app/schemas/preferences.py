"""Schemas for alert preferences and notification channels."""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class AlertPreference(BaseModel):
    """Alert threshold preference for a specific metric."""
    id: UUID
    player_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    metric: Literal['ACWR', 'MONOTONY', 'STRAIN', 'READINESS']
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    level: Literal['warning', 'critical'] = 'warning'
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertPreferenceCreate(BaseModel):
    """Schema for creating/updating alert preferences."""
    metric: Literal['ACWR', 'MONOTONY', 'STRAIN', 'READINESS']
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    level: Literal['warning', 'critical'] = 'warning'


class PlayerPreferences(BaseModel):
    """All preferences for a player."""
    player_id: UUID
    preferences: List[AlertPreference]


class AlertChannel(BaseModel):
    """Notification channel configuration."""
    id: UUID
    player_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    channel: Literal['email', 'webpush']
    address: str
    active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class AlertChannelCreate(BaseModel):
    """Schema for creating notification channels."""
    channel: Literal['email', 'webpush']
    address: str
    active: bool = True


class AlertHistoryItem(BaseModel):
    """Monthly alert statistics."""
    month_start: str
    type: str
    level: Literal['info', 'warning', 'critical']
    count_alerts: int

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Alert history for a player."""
    player_id: UUID
    months: int
    history: List[AlertHistoryItem]

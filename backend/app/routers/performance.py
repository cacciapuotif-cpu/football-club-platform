"""Performance modules API: Technical, Tactical, Psychological, Health."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.performance import (
    HealthMonitoring,
    PsychologicalProfile,
    TacticalCognitive,
    TechnicalStats,
)
from app.models.user import User
from app.schemas.performance import (
    HealthMonitoringCreate,
    HealthMonitoringResponse,
    HealthMonitoringUpdate,
    PsychologicalProfileCreate,
    PsychologicalProfileResponse,
    PsychologicalProfileUpdate,
    TacticalCognitiveCreate,
    TacticalCognitiveResponse,
    TacticalCognitiveUpdate,
    TechnicalStatsCreate,
    TechnicalStatsResponse,
    TechnicalStatsUpdate,
)

router = APIRouter()


# ============ Technical Stats ============
@router.post("/technical", response_model=TechnicalStatsResponse, status_code=status.HTTP_201_CREATED)
async def create_technical_stats(
    data: TechnicalStatsCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create technical stats entry."""
    # Calculate conversion rate if applicable
    conversion_rate = None
    if data.goals is not None and data.shots_on_target and data.shots_on_target > 0:
        conversion_rate = (data.goals / data.shots_on_target) * 100

    technical = TechnicalStats(
        **data.model_dump(),
        organization_id=current_user.organization_id,
        conversion_rate_pct=conversion_rate
    )
    session.add(technical)
    await session.commit()
    await session.refresh(technical)
    return technical


@router.get("/technical", response_model=list[TechnicalStatsResponse])
async def list_technical_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    limit: int = Query(100, le=1000),
):
    """List technical stats."""
    query = select(TechnicalStats).where(TechnicalStats.organization_id == current_user.organization_id)
    if player_id:
        query = query.where(TechnicalStats.player_id == player_id)
    if start_date:
        query = query.where(TechnicalStats.date >= start_date)
    query = query.order_by(TechnicalStats.date.desc()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


# ============ Tactical & Cognitive ============
@router.post("/tactical", response_model=TacticalCognitiveResponse, status_code=status.HTTP_201_CREATED)
async def create_tactical_cognitive(
    data: TacticalCognitiveCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create tactical/cognitive assessment."""
    tactical = TacticalCognitive(**data.model_dump(), organization_id=current_user.organization_id)
    session.add(tactical)
    await session.commit()
    await session.refresh(tactical)
    return tactical


@router.get("/tactical", response_model=list[TacticalCognitiveResponse])
async def list_tactical_cognitive(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    limit: int = Query(100, le=1000),
):
    """List tactical/cognitive assessments."""
    query = select(TacticalCognitive).where(TacticalCognitive.organization_id == current_user.organization_id)
    if player_id:
        query = query.where(TacticalCognitive.player_id == player_id)
    if start_date:
        query = query.where(TacticalCognitive.date >= start_date)
    query = query.order_by(TacticalCognitive.date.desc()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


# ============ Psychological Profile ============
@router.post("/psychological", response_model=PsychologicalProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_psychological_profile(
    data: PsychologicalProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create psychological profile entry."""
    psych = PsychologicalProfile(**data.model_dump(), organization_id=current_user.organization_id)
    session.add(psych)
    await session.commit()
    await session.refresh(psych)
    return psych


@router.get("/psychological", response_model=list[PsychologicalProfileResponse])
async def list_psychological_profiles(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    limit: int = Query(100, le=1000),
):
    """List psychological profiles."""
    query = select(PsychologicalProfile).where(
        PsychologicalProfile.organization_id == current_user.organization_id
    )
    if player_id:
        query = query.where(PsychologicalProfile.player_id == player_id)
    if start_date:
        query = query.where(PsychologicalProfile.date >= start_date)
    query = query.order_by(PsychologicalProfile.date.desc()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


# ============ Health Monitoring ============
@router.post("/health", response_model=HealthMonitoringResponse, status_code=status.HTTP_201_CREATED)
async def create_health_monitoring(
    data: HealthMonitoringCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create health monitoring entry."""
    health = HealthMonitoring(**data.model_dump(), organization_id=current_user.organization_id)
    session.add(health)
    await session.commit()
    await session.refresh(health)
    return health


@router.get("/health", response_model=list[HealthMonitoringResponse])
async def list_health_monitoring(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    player_id: UUID | None = Query(None),
    limit: int = Query(52, le=1000),  # Default 1 year of weeks
):
    """List health monitoring entries."""
    query = select(HealthMonitoring).where(HealthMonitoring.organization_id == current_user.organization_id)
    if player_id:
        query = query.where(HealthMonitoring.player_id == player_id)
    query = query.order_by(HealthMonitoring.week_start_date.desc()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()

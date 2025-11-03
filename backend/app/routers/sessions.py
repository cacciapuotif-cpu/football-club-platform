"""Training sessions API router."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.session import TrainingSession
from app.models.user import User
from app.schemas.session import (
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionUpdate,
)

router = APIRouter()


@router.post("/", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: TrainingSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new training session."""
    training_session = TrainingSession(
        **session_data.model_dump(),
        organization_id=current_user.organization_id
    )
    session.add(training_session)
    await session.commit()
    await session.refresh(training_session)
    return training_session


async def get_demo_org_id(session: AsyncSession) -> UUID:
    """Get the first organization ID for demo purposes (no auth)."""
    from app.models.organization import Organization
    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="No organization found. Please run seed script.")
    return org_id


@router.get("/", response_model=list[TrainingSessionResponse])
async def list_sessions(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: UUID | None = Query(None, description="Filter by team"),
    start_date: date | None = Query(None, description="Filter sessions from this date"),
    end_date: date | None = Query(None, description="Filter sessions until this date"),
):
    """List training sessions for the demo organization (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    query = select(TrainingSession).where(
        TrainingSession.organization_id == org_id
    )

    if team_id:
        query = query.where(TrainingSession.team_id == team_id)
    if start_date:
        query = query.where(TrainingSession.session_date >= start_date)
    if end_date:
        query = query.where(TrainingSession.session_date <= end_date)

    query = query.offset(skip).limit(limit).order_by(TrainingSession.session_date.desc())

    result = await session.execute(query)
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=TrainingSessionResponse)
async def get_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific training session."""
    result = await session.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.organization_id == current_user.organization_id
        )
    )
    training_session = result.scalar_one_or_none()

    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    return training_session


@router.patch("/{session_id}", response_model=TrainingSessionResponse)
async def update_session(
    session_id: UUID,
    session_data: TrainingSessionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a training session."""
    result = await session.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.organization_id == current_user.organization_id
        )
    )
    training_session = result.scalar_one_or_none()

    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(training_session, field, value)

    session.add(training_session)
    await session.commit()
    await session.refresh(training_session)
    return training_session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a training session."""
    result = await session.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.organization_id == current_user.organization_id
        )
    )
    training_session = result.scalar_one_or_none()

    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    await session.delete(training_session)
    await session.commit()
    return None

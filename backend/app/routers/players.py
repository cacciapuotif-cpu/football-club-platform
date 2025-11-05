"""Players API router - CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.organization import Organization
from app.models.player import Player
from app.models.sensor import SensorData
from app.models.session import TrainingSession
from app.schemas.player import PlayerCreate, PlayerResponse, PlayerUpdate
from app.schemas.session import TrainingSessionResponse

router = APIRouter()


async def get_demo_org_id(session: AsyncSession) -> UUID:
    """Get the first organization ID for demo purposes (no auth)."""
    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise HTTPException(status_code=404, detail="No organization found. Please run seed script.")
    return org_id


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new player."""
    # Get demo organization ID (no auth)
    org_id = await get_demo_org_id(session)
    # Create player with organization_id
    player = Player(**player_data.model_dump(), organization_id=org_id)
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.get("/", response_model=list[PlayerResponse])
async def list_players(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: UUID | None = Query(None, description="Filter by team ID"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: str | None = Query(None, description="Filter by primary role (GK, DF, MF, FW)"),
):
    """List all players for the demo organization with optional filters (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    query = select(Player).where(Player.organization_id == org_id)

    # Apply filters
    if team_id:
        query = query.where(Player.team_id == team_id)
    if is_active is not None:
        query = query.where(Player.is_active == is_active)
    if role:
        query = query.where(Player.role_primary == role.upper())

    query = query.offset(skip).limit(limit).order_by(Player.last_name, Player.first_name)

    result = await session.execute(query)
    players = result.scalars().all()
    return players


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific player by ID (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    return player


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: UUID,
    player_data: PlayerUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a player's information (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Update only provided fields
    update_data = player_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)

    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a player (soft delete by setting is_active=False) (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Soft delete
    player.is_active = False
    session.add(player)
    await session.commit()
    return None


@router.get("/{player_id}/sessions", response_model=list[TrainingSessionResponse])
async def get_player_sessions(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get all training sessions for a specific player (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    # First verify the player exists and belongs to the organization
    player_result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == org_id
        )
    )
    player = player_result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    # Get all sessions where this player has sensor data
    query = (
        select(TrainingSession)
        .join(SensorData, SensorData.session_id == TrainingSession.id)
        .where(
            SensorData.player_id == player_id,
            TrainingSession.organization_id == org_id
        )
        .order_by(TrainingSession.session_date.desc())
    )

    result = await session.execute(query)
    sessions = result.scalars().all()
    return sessions

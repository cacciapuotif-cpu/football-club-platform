"""Players API router."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from app.db.database import get_db
from app.models.models import Player
from app.models.enums import PlayerRole
from app.schemas.schemas import PlayerCreate, PlayerUpdate, PlayerResponse

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(
    player_data: PlayerCreate,
    db: Session = Depends(get_db)
):
    """Create a new player."""
    # Check if code already exists
    existing = db.query(Player).filter(Player.code == player_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Player with code '{player_data.code}' already exists"
        )

    # Validate date of birth (player should be between 10 and 25 years old for youth)
    today = date.today()
    age = (today - player_data.date_of_birth).days // 365.25
    if age < 10 or age > 25:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Player age must be between 10 and 25 years (current: {age})"
        )

    # Create player
    player = Player(**player_data.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.get("", response_model=List[PlayerResponse])
def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[PlayerRole] = None,
    category: Optional[str] = None,
    min_age: Optional[int] = Query(None, ge=10, le=25),
    max_age: Optional[int] = Query(None, ge=10, le=25),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all players with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        role: Filter by primary role
        category: Filter by category (e.g., "U17")
        min_age: Minimum age filter
        max_age: Maximum age filter
        search: Search in first_name, last_name, or code
    """
    query = db.query(Player)

    # Apply filters
    if role:
        query = query.filter(Player.primary_role == role)

    if category:
        query = query.filter(Player.category == category)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Player.first_name.ilike(search_term),
                Player.last_name.ilike(search_term),
                Player.code.ilike(search_term)
            )
        )

    # Age filtering requires calculation
    players = query.offset(skip).limit(limit).all()

    if min_age or max_age:
        today = date.today()
        filtered_players = []
        for player in players:
            age = (today - player.date_of_birth).days // 365.25
            if min_age and age < min_age:
                continue
            if max_age and age > max_age:
                continue
            filtered_players.append(player)
        return filtered_players

    return players


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single player by ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    return player


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: UUID,
    player_data: PlayerUpdate,
    db: Session = Depends(get_db)
):
    """Update a player's information."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Update only provided fields
    update_data = player_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(player, key, value)

    db.commit()
    db.refresh(player)

    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a player and all associated sessions/metrics.
    This cascades to all related records.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    db.delete(player)
    db.commit()

    return None

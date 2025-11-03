"""Wellness data API router."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.test import WellnessData
from app.models.player import Player
from app.models.user import User
from app.schemas.wellness import (
    WellnessDataCreate,
    WellnessDataResponse,
    WellnessDataUpdate,
    WellnessSummary,
    WellnessEntry,
)

router = APIRouter()


# === DIAGNOSTICS ENDPOINT ===


@router.get("/_ping")
async def ping_wellness():
    """Diagnostics ping endpoint to verify wellness router is mounted."""
    return {
        "ok": True,
        "service": "wellness",
        "version": "v2",
        "endpoints": [
            "/api/v1/wellness/summary",
            "/api/v1/wellness/player/{player_id}",
            "/api/v1/wellness/_ping"
        ]
    }


# === HELPER FUNCTIONS ===


async def get_demo_org_id(session: AsyncSession) -> UUID:
    """Get the first organization ID for demo purposes (no auth)."""
    from app.models.organization import Organization
    result = await session.execute(select(Organization.id).limit(1))
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise HTTPException(status_code=404, detail="No organization found. Please run seed script.")
    return org_id


@router.post("/", response_model=WellnessDataResponse, status_code=status.HTTP_201_CREATED)
async def create_wellness_data(
    wellness_data: WellnessDataCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create wellness data for a player."""
    wellness = WellnessData(
        **wellness_data.model_dump(),
        organization_id=current_user.organization_id
    )
    session.add(wellness)
    await session.commit()
    await session.refresh(wellness)
    return wellness


# === NEW ENDPOINTS FOR WELLNESS SUMMARY TABLE ===
# IMPORTANT: These specific routes must come BEFORE the generic /{wellness_id} route


@router.get("/summary", response_model=list[WellnessSummary])
async def get_wellness_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    from_date: date | None = Query(None, alias="from", description="Filter wellness sessions from this date"),
    to_date: date | None = Query(None, alias="to", description="Filter wellness sessions to this date"),
    role: str | None = Query(None, description="Filter by player role (GK, DF, MF, FW)"),
    search: str | None = Query(None, description="Search by player name (cognome/nome)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort: Literal[
        "cognome_asc", "cognome_desc",
        "sessions_desc", "sessions_asc",
        "last_entry_desc", "last_entry_asc"
    ] = Query("cognome_asc", description="Sort order"),
):
    """
    Get wellness summary table - list of players with wellness session counts.

    This endpoint uses the vw_wellness_summary view and allows filtering by:
    - Date range (from/to) - recalculates session count for the period
    - Player role
    - Player name search

    Supports pagination and multiple sort options.
    """
    # Get demo organization ID
    org_id = await get_demo_org_id(session)

    # If date filters are present, we need to recalculate the count dynamically
    # Otherwise we can use the pre-aggregated view
    if from_date or to_date:
        # Build dynamic query with date filtering
        base_query = select(
            Player.id.label('player_id'),
            Player.last_name.label('cognome'),
            Player.first_name.label('nome'),
            Player.role_primary.label('ruolo'),
            func.count(WellnessData.date).label('wellness_sessions_count'),
            func.max(WellnessData.date).label('last_entry_date')
        ).select_from(Player).outerjoin(
            WellnessData,
            Player.id == WellnessData.player_id
        ).where(
            Player.organization_id == org_id
        ).group_by(
            Player.id, Player.last_name, Player.first_name, Player.role_primary
        )

        # Apply date filters to the JOIN
        date_conditions = []
        if from_date:
            date_conditions.append(WellnessData.date >= from_date)
        if to_date:
            date_conditions.append(WellnessData.date <= to_date)

        if date_conditions:
            # Re-build with date filtering on wellness data
            base_query = select(
                Player.id.label('player_id'),
                Player.last_name.label('cognome'),
                Player.first_name.label('nome'),
                Player.role_primary.label('ruolo'),
                func.count(WellnessData.date).label('wellness_sessions_count'),
                func.max(WellnessData.date).label('last_entry_date')
            ).select_from(Player).outerjoin(
                WellnessData,
                (Player.id == WellnessData.player_id) &
                (WellnessData.date >= from_date if from_date else True) &
                (WellnessData.date <= to_date if to_date else True)
            ).where(
                Player.organization_id == org_id
            ).group_by(
                Player.id, Player.last_name, Player.first_name, Player.role_primary
            )
    else:
        # Use the view for better performance (no date filtering)
        view_query = text("""
            SELECT
                player_id,
                cognome,
                nome,
                ruolo,
                wellness_sessions_count,
                last_entry_date
            FROM vw_wellness_summary
            WHERE player_id IN (
                SELECT id FROM players WHERE organization_id = :org_id
            )
        """)

        # Build WHERE conditions for role and search
        where_conditions = []
        if role:
            where_conditions.append(f"ruolo = '{role}'")
        if search:
            search_pattern = f"%{search}%"
            where_conditions.append(f"(cognome ILIKE '{search_pattern}' OR nome ILIKE '{search_pattern}')")

        if where_conditions:
            view_query = text(f"""
                SELECT
                    player_id,
                    cognome,
                    nome,
                    ruolo,
                    wellness_sessions_count,
                    last_entry_date
                FROM vw_wellness_summary
                WHERE player_id IN (
                    SELECT id FROM players WHERE organization_id = :org_id
                )
                AND {' AND '.join(where_conditions)}
            """)

        # Apply sorting
        sort_mapping = {
            "cognome_asc": "cognome ASC, nome ASC",
            "cognome_desc": "cognome DESC, nome DESC",
            "sessions_desc": "wellness_sessions_count DESC",
            "sessions_asc": "wellness_sessions_count ASC",
            "last_entry_desc": "last_entry_date DESC NULLS LAST",
            "last_entry_asc": "last_entry_date ASC NULLS LAST",
        }
        order_by = sort_mapping[sort]

        # Add ORDER BY and pagination
        offset = (page - 1) * page_size
        view_query = text(str(view_query) + f" ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}")

        result = await session.execute(view_query, {"org_id": str(org_id)})
        rows = result.fetchall()

        return [
            WellnessSummary(
                player_id=row[0],
                cognome=row[1],
                nome=row[2],
                ruolo=row[3],
                wellness_sessions_count=row[4],
                last_entry_date=row[5]
            )
            for row in rows
        ]

    # If using dynamic query (date filters present), continue with SQLAlchemy
    # Apply role filter
    if role:
        base_query = base_query.where(Player.role_primary == role)

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.where(
            (Player.last_name.ilike(search_pattern)) |
            (Player.first_name.ilike(search_pattern))
        )

    # Apply sorting
    sort_mapping = {
        "cognome_asc": [Player.last_name.asc(), Player.first_name.asc()],
        "cognome_desc": [Player.last_name.desc(), Player.first_name.desc()],
        "sessions_desc": [text("wellness_sessions_count DESC")],
        "sessions_asc": [text("wellness_sessions_count ASC")],
        "last_entry_desc": [text("last_entry_date DESC NULLS LAST")],
        "last_entry_asc": [text("last_entry_date ASC NULLS LAST")],
    }
    for order_clause in sort_mapping[sort]:
        base_query = base_query.order_by(order_clause)

    # Apply pagination
    offset = (page - 1) * page_size
    base_query = base_query.offset(offset).limit(page_size)

    result = await session.execute(base_query)
    rows = result.fetchall()

    return [
        WellnessSummary(
            player_id=row.player_id,
            cognome=row.cognome,
            nome=row.nome,
            ruolo=row.ruolo,
            wellness_sessions_count=row.wellness_sessions_count,
            last_entry_date=row.last_entry_date
        )
        for row in rows
    ]


@router.get("/player/{player_id}", response_model=list[WellnessEntry])
async def get_player_wellness_entries(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    from_date: date | None = Query(None, alias="from", description="Filter from this date"),
    to_date: date | None = Query(None, alias="to", description="Filter to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    Get wellness entries for a specific player.

    Returns paginated list of wellness data entries for the given player,
    ordered by date descending (most recent first).
    """
    # Get demo organization ID
    org_id = await get_demo_org_id(session)

    # Verify player exists and belongs to organization
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

    # Build query for wellness entries
    query = select(WellnessData).where(
        WellnessData.player_id == player_id,
        WellnessData.organization_id == org_id
    )

    # Apply date filters
    if from_date:
        query = query.where(WellnessData.date >= from_date)
    if to_date:
        query = query.where(WellnessData.date <= to_date)

    # Order by date descending and paginate
    offset = (page - 1) * page_size
    query = query.order_by(WellnessData.date.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    wellness_entries = result.scalars().all()

    # Map DB fields to schema fields (with shortened names)
    return [
        WellnessEntry(
            date=entry.date,
            sleep_h=entry.sleep_hours,
            sleep_quality=entry.sleep_quality,
            fatigue=entry.fatigue_rating,
            stress=entry.stress_rating,
            mood=entry.mood_rating,
            doms=entry.doms_rating,
            weight_kg=entry.body_weight_kg,
            notes=entry.notes
        )
        for entry in wellness_entries
    ]


# === GENERIC CRUD ENDPOINTS (must come after specific routes) ===


@router.get("/", response_model=list[WellnessDataResponse])
async def list_wellness_data(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    player_id: UUID | None = Query(None, description="Filter by player"),
    start_date: date | None = Query(None, description="Filter from this date"),
    end_date: date | None = Query(None, description="Filter until this date"),
):
    """List wellness data for the demo organization (no auth)."""
    # Get demo organization ID
    org_id = await get_demo_org_id(session)
    query = select(WellnessData).where(
        WellnessData.organization_id == org_id
    )

    if player_id:
        query = query.where(WellnessData.player_id == player_id)
    if start_date:
        query = query.where(WellnessData.date >= start_date)
    if end_date:
        query = query.where(WellnessData.date <= end_date)

    query = query.offset(skip).limit(limit).order_by(WellnessData.date.desc())

    result = await session.execute(query)
    wellness_list = result.scalars().all()
    return wellness_list


@router.get("/{wellness_id}", response_model=WellnessDataResponse)
async def get_wellness_data(
    wellness_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get specific wellness data entry."""
    result = await session.execute(
        select(WellnessData).where(
            WellnessData.id == wellness_id,
            WellnessData.organization_id == current_user.organization_id
        )
    )
    wellness = result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wellness data not found"
        )

    return wellness


@router.patch("/{wellness_id}", response_model=WellnessDataResponse)
async def update_wellness_data(
    wellness_id: UUID,
    wellness_data: WellnessDataUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update wellness data."""
    result = await session.execute(
        select(WellnessData).where(
            WellnessData.id == wellness_id,
            WellnessData.organization_id == current_user.organization_id
        )
    )
    wellness = result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wellness data not found"
        )

    update_data = wellness_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wellness, field, value)

    session.add(wellness)
    await session.commit()
    await session.refresh(wellness)
    return wellness


@router.delete("/{wellness_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wellness_data(
    wellness_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete wellness data."""
    result = await session.execute(
        select(WellnessData).where(
            WellnessData.id == wellness_id,
            WellnessData.organization_id == current_user.organization_id
        )
    )
    wellness = result.scalar_one_or_none()

    if not wellness:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wellness data not found"
        )

    await session.delete(wellness)
    await session.commit()
    return None

"""Sessions API router."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import (
    Player, Session as SessionModel, MetricsPhysical,
    MetricsTechnical, MetricsTactical, MetricsPsych, AnalyticsOutputs
)
from app.schemas.schemas import SessionCreate, SessionResponse
from app.services.calculations import apply_all_calculations

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new session with all metrics in a single request.
    Calculates derived metrics and analytics automatically.
    """
    # Find player by code
    player = db.query(Player).filter(Player.code == session_data.player_code).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with code '{session_data.player_code}' not found"
        )

    # Create session
    session = SessionModel(
        player_id=player.id,
        **session_data.session.model_dump()
    )
    db.add(session)
    db.flush()  # Get session ID without committing

    # Create metrics
    metrics_phys = MetricsPhysical(
        session_id=session.id,
        **session_data.metrics_physical.model_dump()
    )
    metrics_tech = MetricsTechnical(
        session_id=session.id,
        **session_data.metrics_technical.model_dump()
    )
    metrics_tact = MetricsTactical(
        session_id=session.id,
        **session_data.metrics_tactical.model_dump()
    )
    metrics_psych = MetricsPsych(
        session_id=session.id,
        **session_data.metrics_psych.model_dump()
    )

    db.add_all([metrics_phys, metrics_tech, metrics_tact, metrics_psych])
    db.flush()

    # Calculate all derived metrics
    calculations = apply_all_calculations(
        db=db,
        session_id=str(session.id),
        player_id=str(player.id),
        metrics_physical=metrics_phys,
        metrics_technical=metrics_tech
    )

    # Update metrics with calculated values
    metrics_phys.bmi = calculations["bmi"]
    metrics_tech.pass_accuracy_pct = calculations["pass_accuracy_pct"]
    metrics_tech.shot_accuracy_pct = calculations["shot_accuracy_pct"]
    metrics_tech.dribble_success_pct = calculations["dribble_success_pct"]

    # Create analytics output
    analytics = AnalyticsOutputs(
        session_id=session.id,
        performance_index=calculations["performance_index"],
        progress_index_rolling=calculations["progress_index_rolling"],
        zscore_vs_player_baseline=calculations["zscore_vs_player_baseline"],
        cluster_label=calculations["cluster_label"]
    )
    db.add(analytics)

    # Commit all changes
    db.commit()
    db.refresh(session)

    return session


@router.get("", response_model=List[SessionResponse])
def get_sessions(
    player_id: Optional[UUID] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    session_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get sessions with optional filtering.

    Args:
        player_id: Filter by player ID
        from_date: Start date filter
        to_date: End date filter
        session_type: Filter by session type (TRAINING/MATCH/TEST)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    """
    query = db.query(SessionModel)

    # Apply filters
    if player_id:
        query = query.filter(SessionModel.player_id == player_id)

    if from_date:
        query = query.filter(SessionModel.session_date >= from_date)

    if to_date:
        query = query.filter(SessionModel.session_date <= to_date)

    if session_type:
        query = query.filter(SessionModel.session_type == session_type)

    # Order by date descending
    sessions = query.order_by(
        SessionModel.session_date.desc()
    ).offset(skip).limit(limit).all()

    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single session by ID with all metrics and analytics.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id '{session_id}' not found"
        )

    return session


@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: UUID,
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Update a session and recalculate all derived metrics.
    """
    # Find existing session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id '{session_id}' not found"
        )

    # Update session
    for key, value in session_data.session.model_dump().items():
        setattr(session, key, value)

    # Update metrics
    metrics_phys = db.query(MetricsPhysical).filter(
        MetricsPhysical.session_id == session_id
    ).first()
    if metrics_phys:
        for key, value in session_data.metrics_physical.model_dump().items():
            setattr(metrics_phys, key, value)

    metrics_tech = db.query(MetricsTechnical).filter(
        MetricsTechnical.session_id == session_id
    ).first()
    if metrics_tech:
        for key, value in session_data.metrics_technical.model_dump().items():
            setattr(metrics_tech, key, value)

    metrics_tact = db.query(MetricsTactical).filter(
        MetricsTactical.session_id == session_id
    ).first()
    if metrics_tact:
        for key, value in session_data.metrics_tactical.model_dump().items():
            setattr(metrics_tact, key, value)

    metrics_psych = db.query(MetricsPsych).filter(
        MetricsPsych.session_id == session_id
    ).first()
    if metrics_psych:
        for key, value in session_data.metrics_psych.model_dump().items():
            setattr(metrics_psych, key, value)

    db.flush()

    # Recalculate derived metrics
    calculations = apply_all_calculations(
        db=db,
        session_id=str(session.id),
        player_id=str(session.player_id),
        metrics_physical=metrics_phys,
        metrics_technical=metrics_tech
    )

    # Update calculated values
    if metrics_phys:
        metrics_phys.bmi = calculations["bmi"]
    if metrics_tech:
        metrics_tech.pass_accuracy_pct = calculations["pass_accuracy_pct"]
        metrics_tech.shot_accuracy_pct = calculations["shot_accuracy_pct"]
        metrics_tech.dribble_success_pct = calculations["dribble_success_pct"]

    # Update analytics
    analytics = db.query(AnalyticsOutputs).filter(
        AnalyticsOutputs.session_id == session_id
    ).first()
    if analytics:
        analytics.performance_index = calculations["performance_index"]
        analytics.progress_index_rolling = calculations["progress_index_rolling"]
        analytics.zscore_vs_player_baseline = calculations["zscore_vs_player_baseline"]
        analytics.cluster_label = calculations["cluster_label"]

    db.commit()
    db.refresh(session)

    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a session and all associated metrics/analytics.
    This cascades to all related records.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id '{session_id}' not found"
        )

    db.delete(session)
    db.commit()

    return None

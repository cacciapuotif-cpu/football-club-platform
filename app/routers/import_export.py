"""Import/Export API router."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date
import csv
import io
import json

from app.db.database import get_db
from app.models.models import (
    Player, Session as SessionModel, MetricsPhysical,
    MetricsTechnical, MetricsTactical, MetricsPsych
)

router = APIRouter(prefix="", tags=["Import/Export"])


@router.post("/import/csv")
async def import_sessions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import sessions from CSV file.

    Expected CSV columns (see assets/templates/session_import_template.csv):
    - player_code
    - session_date (YYYY-MM-DD)
    - session_type
    - minutes_played
    - ... (all session and metrics fields)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )

    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))

        imported_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 is header)
            try:
                # Find player
                player_code = row.get('player_code', '').strip()
                if not player_code:
                    errors.append(f"Row {row_num}: Missing player_code")
                    continue

                player = db.query(Player).filter(Player.code == player_code).first()
                if not player:
                    errors.append(f"Row {row_num}: Player '{player_code}' not found")
                    continue

                # Parse session data
                session_date_str = row.get('session_date', '').strip()
                if not session_date_str:
                    errors.append(f"Row {row_num}: Missing session_date")
                    continue

                session_date = date.fromisoformat(session_date_str)

                # Create session (simplified - you should add all fields)
                session = SessionModel(
                    player_id=player.id,
                    session_date=session_date,
                    session_type=row.get('session_type', 'TRAINING'),
                    minutes_played=int(row.get('minutes_played', 0) or 0),
                    coach_rating=float(row.get('coach_rating') or 0) if row.get('coach_rating') else None,
                    notes=row.get('notes'),
                    status=row.get('status', 'OK')
                )
                db.add(session)
                db.flush()

                # Create metrics (add all fields from CSV)
                # Physical
                metrics_phys = MetricsPhysical(
                    session_id=session.id,
                    resting_hr_bpm=int(row.get('resting_hr_bpm', 60) or 60),
                    distance_km=float(row.get('distance_km', 0) or 0),
                    sprints_over_25kmh=int(row.get('sprints_over_25kmh', 0) or 0),
                    rpe=float(row.get('rpe', 5) or 5)
                )
                db.add(metrics_phys)

                # Technical
                metrics_tech = MetricsTechnical(
                    session_id=session.id,
                    passes_attempted=int(row.get('passes_attempted', 0) or 0),
                    passes_completed=int(row.get('passes_completed', 0) or 0),
                    progressive_passes=int(row.get('progressive_passes', 0) or 0),
                    shots=int(row.get('shots', 0) or 0),
                    shots_on_target=int(row.get('shots_on_target', 0) or 0),
                    successful_dribbles=int(row.get('successful_dribbles', 0) or 0),
                    failed_dribbles=int(row.get('failed_dribbles', 0) or 0),
                    ball_losses=int(row.get('ball_losses', 0) or 0),
                    ball_recoveries=int(row.get('ball_recoveries', 0) or 0)
                )
                db.add(metrics_tech)

                # Tactical
                metrics_tact = MetricsTactical(
                    session_id=session.id,
                    interceptions=int(row.get('interceptions', 0) or 0),
                    pressures=int(row.get('pressures', 0) or 0)
                )
                db.add(metrics_tact)

                # Psychological
                metrics_psych = MetricsPsych(
                    session_id=session.id,
                    motivation=int(row.get('motivation') or 7) if row.get('motivation') else None,
                    attention_score=int(row.get('attention_score') or 70) if row.get('attention_score') else None
                )
                db.add(metrics_psych)

                imported_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue

        db.commit()

        return {
            "imported": imported_count,
            "errors": errors,
            "total_rows": row_num - 1  # Exclude header
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV: {str(e)}"
        )


@router.get("/export/sessions.csv")
def export_sessions_csv(
    player_id: Optional[UUID] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """
    Export sessions to CSV format.

    Args:
        player_id: Filter by player ID
        from_date: Start date filter
        to_date: End date filter
    """
    # Build query
    query = db.query(SessionModel)

    if player_id:
        query = query.filter(SessionModel.player_id == player_id)
    if from_date:
        query = query.filter(SessionModel.session_date >= from_date)
    if to_date:
        query = query.filter(SessionModel.session_date <= to_date)

    sessions = query.order_by(SessionModel.session_date.desc()).all()

    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sessions found for export"
        )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'player_code', 'player_name', 'session_date', 'session_type',
        'minutes_played', 'coach_rating', 'performance_index',
        'distance_km', 'sprints_over_25kmh', 'resting_hr_bpm', 'rpe',
        'pass_accuracy_pct', 'progressive_passes', 'successful_dribbles',
        'interceptions', 'xg', 'xa', 'motivation', 'attention_score'
    ])

    # Write data
    for session in sessions:
        player = session.player
        phys = session.metrics_physical
        tech = session.metrics_technical
        tact = session.metrics_tactical
        psych = session.metrics_psych
        analytics = session.analytics_outputs

        writer.writerow([
            player.code,
            f"{player.first_name} {player.last_name}",
            session.session_date.isoformat(),
            session.session_type.value,
            session.minutes_played,
            float(session.coach_rating) if session.coach_rating else '',
            float(analytics.performance_index) if analytics else '',
            float(phys.distance_km) if phys else '',
            phys.sprints_over_25kmh if phys else '',
            phys.resting_hr_bpm if phys else '',
            float(phys.rpe) if phys else '',
            float(tech.pass_accuracy_pct) if tech and tech.pass_accuracy_pct else '',
            tech.progressive_passes if tech else '',
            tech.successful_dribbles if tech else '',
            tact.interceptions if tact else '',
            float(tact.xg) if tact and tact.xg else '',
            float(tact.xa) if tact and tact.xa else '',
            psych.motivation if psych else '',
            psych.attention_score if psych else ''
        ])

    # Prepare response
    output.seek(0)
    filename = f"sessions_export_{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/sessions.json")
def export_sessions_json(
    player_id: Optional[UUID] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """
    Export sessions to JSON format.

    Args:
        player_id: Filter by player ID
        from_date: Start date filter
        to_date: End date filter
    """
    # Build query
    query = db.query(SessionModel)

    if player_id:
        query = query.filter(SessionModel.player_id == player_id)
    if from_date:
        query = query.filter(SessionModel.session_date >= from_date)
    if to_date:
        query = query.filter(SessionModel.session_date <= to_date)

    sessions = query.order_by(SessionModel.session_date.desc()).all()

    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sessions found for export"
        )

    # Build JSON structure
    export_data = []
    for session in sessions:
        player = session.player

        session_data = {
            "player": {
                "code": player.code,
                "name": f"{player.first_name} {player.last_name}",
                "role": player.primary_role.value
            },
            "session": {
                "date": session.session_date.isoformat(),
                "type": session.session_type.value,
                "minutes_played": session.minutes_played,
                "coach_rating": float(session.coach_rating) if session.coach_rating else None
            },
            "metrics": {},
            "analytics": {}
        }

        if session.metrics_physical:
            phys = session.metrics_physical
            session_data["metrics"]["physical"] = {
                "distance_km": float(phys.distance_km),
                "sprints_over_25kmh": phys.sprints_over_25kmh,
                "resting_hr_bpm": phys.resting_hr_bpm,
                "rpe": float(phys.rpe)
            }

        if session.metrics_technical:
            tech = session.metrics_technical
            session_data["metrics"]["technical"] = {
                "pass_accuracy_pct": float(tech.pass_accuracy_pct) if tech.pass_accuracy_pct else None,
                "progressive_passes": tech.progressive_passes,
                "successful_dribbles": tech.successful_dribbles
            }

        if session.analytics_outputs:
            analytics = session.analytics_outputs
            session_data["analytics"] = {
                "performance_index": float(analytics.performance_index),
                "progress_index_rolling": float(analytics.progress_index_rolling) if analytics.progress_index_rolling else None,
                "zscore_vs_baseline": float(analytics.zscore_vs_player_baseline) if analytics.zscore_vs_player_baseline else None,
                "cluster_label": analytics.cluster_label
            }

        export_data.append(session_data)

    return JSONResponse(content={
        "export_date": date.today().isoformat(),
        "total_sessions": len(export_data),
        "sessions": export_data
    })

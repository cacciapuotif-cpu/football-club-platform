"""Analytics API router."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import statistics

from app.db.database import get_db
from app.models.models import (
    Player, Session as SessionModel, AnalyticsOutputs,
    MetricsPhysical, MetricsTechnical, MetricsTactical, MetricsPsych
)
from app.schemas.schemas import (
    PlayerTrendResponse, PlayerSummaryResponse, PlayerCompareResponse
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/players/{player_id}/trend", response_model=List[PlayerTrendResponse])
def get_player_trend(
    player_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get time series trend data for a player.
    Returns session_date, performance_index, progress_index_rolling and key metrics.
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Get sessions with all metrics
    sessions = db.query(SessionModel).filter(
        SessionModel.player_id == player_id
    ).order_by(
        SessionModel.session_date.desc()
    ).limit(limit).all()

    if not sessions:
        return []

    trend_data = []
    for session in sessions:
        analytics = session.analytics_outputs
        phys = session.metrics_physical
        tech = session.metrics_technical
        tact = session.metrics_tactical

        trend_data.append(PlayerTrendResponse(
            session_date=session.session_date,
            performance_index=analytics.performance_index if analytics else 0,
            progress_index_rolling=analytics.progress_index_rolling if analytics else None,
            distance_km=phys.distance_km if phys else None,
            pass_accuracy_pct=tech.pass_accuracy_pct if tech else None,
            progressive_passes=tech.progressive_passes if tech else None,
            interceptions=tact.interceptions if tact else None,
            successful_dribbles=tech.successful_dribbles if tech else None,
            sprints_over_25kmh=phys.sprints_over_25kmh if phys else None,
            rpe=phys.rpe if phys else None,
            coach_rating=session.coach_rating
        ))

    # Return in chronological order (oldest first)
    return list(reversed(trend_data))


@router.get("/players/{player_id}/summary", response_model=PlayerSummaryResponse)
def get_player_summary(
    player_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive summary statistics for a player.
    Includes overall stats split by training vs match.
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Get all sessions
    sessions = db.query(SessionModel).filter(
        SessionModel.player_id == player_id
    ).all()

    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sessions found for player '{player_id}'"
        )

    # Overall statistics
    performance_indices = []
    training_indices = []
    match_indices = []

    for session in sessions:
        if session.analytics_outputs:
            perf_idx = float(session.analytics_outputs.performance_index)
            performance_indices.append(perf_idx)

            if session.session_type.value == "TRAINING":
                training_indices.append(perf_idx)
            elif session.session_type.value == "MATCH":
                match_indices.append(perf_idx)

    # Get latest z-score
    latest_session = sorted(sessions, key=lambda s: s.session_date, reverse=True)[0]
    current_zscore = None
    if latest_session.analytics_outputs:
        current_zscore = latest_session.analytics_outputs.zscore_vs_player_baseline

    # Aggregate training stats
    training_stats = {
        "count": len(training_indices),
        "avg_performance": round(statistics.mean(training_indices), 2) if training_indices else 0,
        "max_performance": round(max(training_indices), 2) if training_indices else 0,
        "min_performance": round(min(training_indices), 2) if training_indices else 0
    }

    # Aggregate match stats
    match_stats = {
        "count": len(match_indices),
        "avg_performance": round(statistics.mean(match_indices), 2) if match_indices else 0,
        "max_performance": round(max(match_indices), 2) if match_indices else 0,
        "min_performance": round(min(match_indices), 2) if match_indices else 0
    }

    return PlayerSummaryResponse(
        player_id=player.id,
        player_name=f"{player.first_name} {player.last_name}",
        total_sessions=len(sessions),
        avg_performance_index=round(statistics.mean(performance_indices), 2),
        max_performance_index=round(max(performance_indices), 2),
        min_performance_index=round(min(performance_indices), 2),
        current_baseline_zscore=current_zscore,
        training_stats=training_stats,
        match_stats=match_stats
    )


@router.get("/compare", response_model=List[PlayerCompareResponse])
def compare_players(
    player_ids: str = Query(..., description="Comma-separated player UUIDs"),
    recent_n: int = Query(10, ge=1, le=50, description="Number of recent sessions to compare"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple players based on their recent N sessions.

    Args:
        player_ids: Comma-separated list of player UUIDs
        recent_n: Number of recent sessions to include in comparison
    """
    # Parse player IDs
    try:
        ids = [UUID(pid.strip()) for pid in player_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid player ID format"
        )

    if len(ids) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare more than 10 players at once"
        )

    comparison_data = []

    for player_id in ids:
        # Get player
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            continue

        # Get recent sessions
        sessions = db.query(SessionModel).filter(
            SessionModel.player_id == player_id
        ).order_by(
            SessionModel.session_date.desc()
        ).limit(recent_n).all()

        if not sessions:
            continue

        # Calculate average performance index
        perf_indices = []
        key_metrics = {
            "avg_distance_km": [],
            "avg_pass_accuracy": [],
            "avg_progressive_passes": [],
            "avg_sprints": [],
            "avg_interceptions": []
        }

        for session in sessions:
            if session.analytics_outputs:
                perf_indices.append(float(session.analytics_outputs.performance_index))

            if session.metrics_physical:
                key_metrics["avg_distance_km"].append(float(session.metrics_physical.distance_km))
                key_metrics["avg_sprints"].append(session.metrics_physical.sprints_over_25kmh)

            if session.metrics_technical:
                if session.metrics_technical.pass_accuracy_pct:
                    key_metrics["avg_pass_accuracy"].append(
                        float(session.metrics_technical.pass_accuracy_pct)
                    )
                key_metrics["avg_progressive_passes"].append(
                    session.metrics_technical.progressive_passes
                )

            if session.metrics_tactical:
                key_metrics["avg_interceptions"].append(session.metrics_tactical.interceptions)

        # Aggregate metrics
        aggregated_metrics = {}
        for key, values in key_metrics.items():
            if values:
                aggregated_metrics[key] = round(statistics.mean(values), 2)
            else:
                aggregated_metrics[key] = 0

        comparison_data.append(PlayerCompareResponse(
            player_id=player.id,
            player_name=f"{player.first_name} {player.last_name}",
            avg_performance_index=round(statistics.mean(perf_indices), 2) if perf_indices else 0,
            recent_sessions_count=len(sessions),
            key_metrics=aggregated_metrics
        ))

    if not comparison_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for the specified players"
        )

    # Sort by avg_performance_index descending
    comparison_data.sort(key=lambda x: x.avg_performance_index, reverse=True)

    return comparison_data


@router.get("/players/{player_id}/wellness-trends")
def get_player_wellness_trends(
    player_id: UUID,
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get wellness trends for a player over time.
    Returns time series data for sleep, mood, stress, motivation, fatigue (RPE).
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Calculate start date
    from datetime import timedelta
    start_date = date.today() - timedelta(days=days)

    # Get sessions with metrics
    sessions = db.query(SessionModel).filter(
        SessionModel.player_id == player_id,
        SessionModel.session_date >= start_date
    ).order_by(
        SessionModel.session_date.asc()
    ).all()

    # Prepare trend data
    trends = {
        "dates": [],
        "sleep_hours": [],
        "sleep_quality": [],
        "mood": [],
        "stress": [],
        "motivation": [],
        "rpe": [],
        "resting_hr": [],
    }

    for session in sessions:
        trends["dates"].append(session.session_date.isoformat())

        # Physical metrics
        if session.metrics_physical:
            trends["sleep_hours"].append(float(session.metrics_physical.sleep_hours) if session.metrics_physical.sleep_hours else None)
            trends["rpe"].append(float(session.metrics_physical.rpe) if session.metrics_physical.rpe else None)
            trends["resting_hr"].append(session.metrics_physical.resting_hr_bpm if session.metrics_physical.resting_hr_bpm else None)
        else:
            trends["sleep_hours"].append(None)
            trends["rpe"].append(None)
            trends["resting_hr"].append(None)

        # Psychological metrics
        if session.metrics_psych:
            trends["sleep_quality"].append(session.metrics_psych.sleep_quality if session.metrics_psych.sleep_quality else None)
            trends["mood"].append(session.metrics_psych.mood_pre if session.metrics_psych.mood_pre else None)
            trends["stress"].append(session.metrics_psych.stress_management if session.metrics_psych.stress_management else None)
            trends["motivation"].append(session.metrics_psych.motivation if session.metrics_psych.motivation else None)
        else:
            trends["sleep_quality"].append(None)
            trends["mood"].append(None)
            trends["stress"].append(None)
            trends["motivation"].append(None)

    return trends


@router.get("/players/{player_id}/training-load")
def get_player_training_load(
    player_id: UUID,
    days: int = Query(42, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get training load analysis for a player.
    Returns daily training loads based on RPE and minutes played.
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found"
        )

    # Calculate start date
    from datetime import timedelta
    start_date = date.today() - timedelta(days=days)

    # Get sessions with physical metrics
    sessions = db.query(SessionModel).filter(
        SessionModel.player_id == player_id,
        SessionModel.session_date >= start_date
    ).order_by(
        SessionModel.session_date.asc()
    ).all()

    # Calculate training load (RPE * minutes)
    daily_loads = []
    cumulative_load = []
    total = 0

    for session in sessions:
        if session.metrics_physical and session.metrics_physical.rpe:
            load = float(session.metrics_physical.rpe) * session.minutes_played
        else:
            load = 0

        daily_loads.append({
            "date": session.session_date.isoformat(),
            "load": round(load, 2),
            "rpe": float(session.metrics_physical.rpe) if session.metrics_physical and session.metrics_physical.rpe else None,
            "duration": session.minutes_played
        })
        total += load
        cumulative_load.append(round(total, 2))

    # Calculate ACWR (Acute:Chronic Workload Ratio) for each day
    acwr_values = []
    for i, item in enumerate(daily_loads):
        if i >= 27:  # Need at least 28 days of data
            # Acute load: last 7 days
            acute = sum(daily_loads[j]["load"] for j in range(i-6, i+1))
            # Chronic load: last 28 days
            chronic = sum(daily_loads[j]["load"] for j in range(i-27, i+1))

            acwr = round(acute / chronic, 2) if chronic > 0 else 0
            acwr_values.append({
                "date": item["date"],
                "acwr": acwr,
                "acute_load": round(acute, 2),
                "chronic_load": round(chronic, 2)
            })
        else:
            acwr_values.append({
                "date": item["date"],
                "acwr": None,
                "acute_load": None,
                "chronic_load": None
            })

    return {
        "daily_loads": daily_loads,
        "cumulative_load": cumulative_load,
        "acwr": acwr_values,
        "total_load": round(total, 2),
        "average_daily_load": round(total / len(daily_loads), 2) if daily_loads else 0
    }

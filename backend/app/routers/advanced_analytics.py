"""Advanced analytics and ML-powered scouting endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.player import Player
from app.models.player_stats import PlayerStats
from app.services.advanced_ml_algorithms import advanced_ml

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# PYDANTIC SCHEMAS
# ============================================


class PlayerSummary(BaseModel):
    """Player summary information."""
    id: str
    name: str
    position: str
    age: int
    team_id: Optional[str]
    overall_rating: float


class AggregateStats(BaseModel):
    """Aggregated statistics over period."""
    matches: int
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    passes_attempted: int
    passes_completed: int
    tackles_attempted: int
    tackles_success: int
    interceptions: int
    distance_covered: int
    performance_index: float
    influence_score: float
    shot_accuracy: float
    pass_accuracy: float
    tackle_success: float
    avg_distance: float


class PositionRanking(BaseModel):
    """Position ranking information."""
    position: str
    current_rank: int
    total_players: int
    percentile: float


class PlayerAnalysisResponse(BaseModel):
    """Complete player analysis response."""
    player: PlayerSummary
    analytics: dict
    recent_matches: List[dict]


class ScoutingRecommendation(BaseModel):
    """Scouting recommendation."""
    player: dict
    analytics: dict
    recommendation: str
    confidence: int


class ScoutingResponse(BaseModel):
    """Scouting recommendations response."""
    team_id: str
    filters: dict
    recommendations: List[ScoutingRecommendation]
    summary: dict


class TeamAnalysisResponse(BaseModel):
    """Team analysis response."""
    team_id: str
    total_players: int
    average_rating: float
    position_distribution: dict
    performance_by_position: dict
    top_performers: List[dict]
    areas_for_improvement: List[str]


class TrendDataPoint(BaseModel):
    """Performance trend data point."""
    date: str
    performance_index: float
    influence_score: float
    form: float


class PerformanceTrendResponse(BaseModel):
    """Performance trend response."""
    player_id: str
    period: str
    trend_data: List[TrendDataPoint]
    summary: dict


# ============================================
# ENDPOINTS
# ============================================


@router.get(
    "/players/{player_id}/analysis",
    response_model=PlayerAnalysisResponse,
    summary="Get comprehensive player analysis",
    description="Retrieve detailed analytics including aggregate stats, performance trends, and strengths/improvements"
)
async def get_player_analysis(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2024-2025')"),
    matches: int = Query(10, ge=1, le=50, description="Number of recent matches to analyze")
):
    """Get comprehensive player analysis with ML insights."""
    # Fetch player
    player_stmt = select(Player).where(Player.id == player_id)
    player_result = await session.execute(player_stmt)
    player = player_result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found"
        )

    # Fetch stats
    stats_filters = [PlayerStats.player_id == player_id]
    if season:
        stats_filters.append(PlayerStats.season == season)

    stats_stmt = (
        select(PlayerStats)
        .where(and_(*stats_filters))
        .order_by(PlayerStats.date.desc())
        .limit(matches)
    )
    stats_result = await session.execute(stats_stmt)
    stats = stats_result.scalars().all()

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No statistics found for player {player_id}"
        )

    # Calculate aggregate stats
    aggregate_stats = _calculate_aggregate_stats(stats)

    # Calculate performance trend
    performance_trend = _calculate_performance_trend(stats)

    # Predict form
    form_prediction = await advanced_ml.predict_player_form(
        session, str(player_id), matches_to_analyze=matches
    )

    # Get position ranking
    position_ranking = await _get_position_ranking(
        session, player.role_primary, aggregate_stats["performance_index"], player.organization_id
    )

    # Calculate age
    age = (datetime.now().date() - player.date_of_birth).days // 365

    # Identify strengths and improvements
    strengths = _identify_strengths(aggregate_stats, player.role_primary)
    improvements = _identify_improvements(aggregate_stats, player.role_primary)

    return PlayerAnalysisResponse(
        player=PlayerSummary(
            id=str(player.id),
            name=f"{player.first_name} {player.last_name}",
            position=player.role_primary,
            age=age,
            team_id=str(player.team_id) if player.team_id else None,
            overall_rating=float(player.overall_rating) if player.overall_rating else 6.0
        ),
        analytics={
            "aggregate_stats": aggregate_stats,
            "performance_trend": performance_trend,
            "form_prediction": form_prediction,
            "position_ranking": position_ranking,
            "strengths": strengths,
            "improvements": improvements
        },
        recent_matches=[
            {
                "match_id": str(stat.match_id) if stat.match_id else str(stat.session_id),
                "date": stat.date.isoformat(),
                "performance_index": float(stat.performance_index),
                "influence_score": float(stat.influence_score),
                "goals": stat.goals,
                "assists": stat.assists
            }
            for stat in stats[:5]
        ]
    )


@router.get(
    "/scouting/teams/{team_id}/recommendations",
    response_model=ScoutingResponse,
    summary="Get AI-powered scouting recommendations",
    description="Generate intelligent player recommendations based on ML analysis and team needs"
)
async def get_scouting_recommendations(
    team_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    position: Optional[str] = Query(None, description="Filter by position (GK, DF, MF, FW)"),
    max_age: Optional[int] = Query(None, ge=15, le=40, description="Maximum age"),
    max_budget: Optional[float] = Query(None, ge=0, description="Maximum market value in EUR"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum overall rating")
):
    """Get AI-powered scouting recommendations for a team."""
    # Fetch team to get organization_id
    from app.models.team import Team
    team_stmt = select(Team).where(Team.id == team_id)
    team_result = await session.execute(team_stmt)
    team = team_result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )

    # Get recommendations
    recommendations = await advanced_ml.get_scouting_recommendations(
        session=session,
        team_id=str(team_id),
        organization_id=str(team.organization_id),
        position=position,
        max_age=max_age,
        max_budget=max_budget,
        min_rating=min_rating
    )

    # Calculate summary
    summary = {
        "total_players": len(recommendations),
        "strong_buys": sum(1 for r in recommendations if r["recommendation"] == "STRONG_BUY"),
        "buys": sum(1 for r in recommendations if r["recommendation"] == "BUY"),
        "considers": sum(1 for r in recommendations if r["recommendation"] == "CONSIDER")
    }

    return ScoutingResponse(
        team_id=str(team_id),
        filters={
            "position": position,
            "max_age": max_age,
            "max_budget": max_budget,
            "min_rating": min_rating
        },
        recommendations=[ScoutingRecommendation(**r) for r in recommendations],
        summary=summary
    )


@router.get(
    "/teams/{team_id}/analysis",
    response_model=TeamAnalysisResponse,
    summary="Get comprehensive team analysis",
    description="Analyze team composition, performance distribution, and identify improvement areas"
)
async def get_team_analysis(
    team_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    season: Optional[str] = Query(None, description="Filter by season")
):
    """Get comprehensive team analysis."""
    # Fetch all players in team
    players_stmt = select(Player).where(Player.team_id == team_id, Player.is_active == True)
    players_result = await session.execute(players_stmt)
    players = players_result.scalars().all()

    if not players:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active players found for team {team_id}"
        )

    # Calculate team metrics
    total_players = len(players)
    ratings = [p.overall_rating for p in players if p.overall_rating]
    average_rating = sum(ratings) / len(ratings) if ratings else 0.0

    # Position distribution
    position_distribution = {}
    for player in players:
        pos = player.role_primary
        position_distribution[pos] = position_distribution.get(pos, 0) + 1

    # Performance by position
    performance_by_position = {}
    for pos in position_distribution.keys():
        pos_players = [p for p in players if p.role_primary == pos]
        pos_ratings = [p.overall_rating for p in pos_players if p.overall_rating]
        performance_by_position[pos] = (
            sum(pos_ratings) / len(pos_ratings) if pos_ratings else 0.0
        )

    # Top performers
    top_performers = sorted(
        [p for p in players if p.overall_rating and p.overall_rating > 7.0],
        key=lambda p: p.overall_rating,
        reverse=True
    )[:5]

    top_performers_data = [
        {
            "id": str(p.id),
            "name": f"{p.first_name} {p.last_name}",
            "position": p.role_primary,
            "rating": float(p.overall_rating)
        }
        for p in top_performers
    ]

    # Identify improvement areas
    improvements = []
    if not position_distribution.get("DF") or position_distribution.get("DF", 0) < 4:
        improvements.append("Defensive Depth")
    if not position_distribution.get("FW") or position_distribution.get("FW", 0) < 3:
        improvements.append("Attacking Options")
    if performance_by_position.get("DF", 0) < 6.5:
        improvements.append("Defensive Quality")
    if performance_by_position.get("FW", 0) < 6.8:
        improvements.append("Finishing Quality")

    return TeamAnalysisResponse(
        team_id=str(team_id),
        total_players=total_players,
        average_rating=round(average_rating, 2),
        position_distribution=position_distribution,
        performance_by_position={k: round(v, 2) for k, v in performance_by_position.items()},
        top_performers=top_performers_data,
        areas_for_improvement=improvements
    )


@router.get(
    "/players/{player_id}/trend",
    response_model=PerformanceTrendResponse,
    summary="Get player performance trend",
    description="Analyze performance trends over a specified time period"
)
async def get_performance_trend(
    player_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    period_days: int = Query(30, ge=7, le=365, description="Period in days to analyze")
):
    """Get player performance trend over time."""
    start_date = datetime.now().date() - timedelta(days=period_days)

    # Fetch stats for period
    stats_stmt = (
        select(PlayerStats)
        .where(
            and_(
                PlayerStats.player_id == player_id,
                PlayerStats.date >= start_date
            )
        )
        .order_by(PlayerStats.date.asc())
    )
    stats_result = await session.execute(stats_stmt)
    stats = stats_result.scalars().all()

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No statistics found for player {player_id} in the specified period"
        )

    # Build trend data
    trend_data = [
        TrendDataPoint(
            date=stat.date.isoformat(),
            performance_index=float(stat.performance_index),
            influence_score=float(stat.influence_score),
            form=float(stat.performance_index) / 10
        )
        for stat in stats
    ]

    # Calculate summary metrics
    performances = [d.performance_index for d in trend_data]
    avg_performance = sum(performances) / len(performances)
    trend_direction = _analyze_trend(performances)
    consistency = _calculate_consistency(performances)

    return PerformanceTrendResponse(
        player_id=str(player_id),
        period=f"{period_days} days",
        trend_data=trend_data,
        summary={
            "average_performance": round(avg_performance, 2),
            "trend": trend_direction,
            "consistency": round(consistency, 1)
        }
    )


# ============================================
# HELPER FUNCTIONS
# ============================================


def _calculate_aggregate_stats(stats: List[PlayerStats]) -> dict:
    """Calculate aggregate statistics from list of PlayerStats."""
    totals = {
        "matches": len(stats),
        "goals": sum(s.goals for s in stats),
        "assists": sum(s.assists for s in stats),
        "shots": sum(s.shots for s in stats),
        "shots_on_target": sum(s.shots_on_target for s in stats),
        "passes_attempted": sum(s.passes_attempted for s in stats),
        "passes_completed": sum(s.passes_completed for s in stats),
        "tackles_attempted": sum(s.tackles_attempted for s in stats),
        "tackles_success": sum(s.tackles_success for s in stats),
        "interceptions": sum(s.interceptions for s in stats),
        "distance_covered": sum(s.distance_covered_m for s in stats)
    }

    # Calculate averages
    avg_performance = sum(s.performance_index for s in stats) / len(stats)
    avg_influence = sum(s.influence_score for s in stats) / len(stats)

    # Calculate percentages
    shot_accuracy = (totals["shots_on_target"] / totals["shots"] * 100) if totals["shots"] > 0 else 0
    pass_accuracy = (totals["passes_completed"] / totals["passes_attempted"] * 100) if totals["passes_attempted"] > 0 else 0
    tackle_success = (totals["tackles_success"] / totals["tackles_attempted"] * 100) if totals["tackles_attempted"] > 0 else 0
    avg_distance = totals["distance_covered"] / len(stats)

    return {
        **totals,
        "performance_index": round(avg_performance, 2),
        "influence_score": round(avg_influence, 2),
        "shot_accuracy": round(shot_accuracy, 2),
        "pass_accuracy": round(pass_accuracy, 2),
        "tackle_success": round(tackle_success, 2),
        "avg_distance": round(avg_distance, 0)
    }


def _calculate_performance_trend(stats: List[PlayerStats]) -> str:
    """Determine performance trend (improving/declining/stable)."""
    if len(stats) < 2:
        return "stable"

    recent = [s.performance_index for s in stats[:3]]
    older = [s.performance_index for s in stats[-3:]]

    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)

    difference = recent_avg - older_avg
    if difference > 2:
        return "improving"
    elif difference < -2:
        return "declining"
    return "stable"


async def _get_position_ranking(
    session: AsyncSession,
    position: str,
    performance: float,
    organization_id: UUID
) -> dict:
    """Get player ranking within position."""
    # Fetch all players in same position
    stmt = select(Player).where(
        and_(
            Player.role_primary == position,
            Player.organization_id == organization_id,
            Player.is_active == True
        )
    )
    result = await session.execute(stmt)
    players = result.scalars().all()

    # Get average performance for each
    ranked_players = []
    for player in players:
        stats_stmt = (
            select(PlayerStats)
            .where(PlayerStats.player_id == player.id)
            .order_by(PlayerStats.date.desc())
            .limit(10)
        )
        stats_result = await session.execute(stats_stmt)
        stats = stats_result.scalars().all()

        if stats:
            avg_perf = sum(s.performance_index for s in stats) / len(stats)
            ranked_players.append({"id": player.id, "performance": avg_perf})

    # Sort and find rank
    ranked_players.sort(key=lambda x: x["performance"], reverse=True)
    current_rank = next(
        (i + 1 for i, p in enumerate(ranked_players) if p["performance"] <= performance),
        len(ranked_players) + 1
    )

    total = len(ranked_players)
    percentile = ((total - current_rank) / total * 100) if total > 0 else 0

    return {
        "position": position,
        "current_rank": current_rank,
        "total_players": total,
        "percentile": round(percentile, 1)
    }


def _identify_strengths(stats: dict, position: str) -> List[str]:
    """Identify player strengths based on stats."""
    strengths = []

    if stats["shot_accuracy"] > 40:
        strengths.append("Finishing")
    if stats["pass_accuracy"] > 80:
        strengths.append("Passing Accuracy")
    if stats["tackle_success"] > 70:
        strengths.append("Tackling")
    if stats["avg_distance"] > 10000:
        strengths.append("Work Rate")
    if stats["influence_score"] > 7.5:
        strengths.append("Game Influence")

    return strengths[:3]


def _identify_improvements(stats: dict, position: str) -> List[str]:
    """Identify areas for improvement."""
    improvements = []

    if stats["pass_accuracy"] < 70:
        improvements.append("Passing Consistency")
    if stats["tackle_success"] < 50 and position in ["DF", "MF"]:
        improvements.append("Defensive Positioning")
    if stats["shot_accuracy"] < 30 and position in ["FW", "MF"]:
        improvements.append("Shot Selection")
    if stats["avg_distance"] < 8000:
        improvements.append("Physical Conditioning")

    return improvements[:2]


def _analyze_trend(data: List[float]) -> str:
    """Analyze trend direction."""
    if len(data) < 2:
        return "stable"

    first_half = data[:len(data)//2]
    second_half = data[len(data)//2:]

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    if second_avg > first_avg + 1:
        return "improving"
    elif second_avg < first_avg - 1:
        return "declining"
    return "stable"


def _calculate_consistency(data: List[float]) -> float:
    """Calculate performance consistency score (0-100)."""
    if len(data) < 2:
        return 100.0

    average = sum(data) / len(data)
    variance = sum((x - average) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5

    consistency = max(0, 100 - (std_dev * 10))
    return consistency

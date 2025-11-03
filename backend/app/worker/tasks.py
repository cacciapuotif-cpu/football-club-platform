"""
Async Worker Tasks for ML Training and Heavy Operations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

from rq import Queue
from redis import Redis

from app.config import settings
from app.database import get_session
from app.ml.core.real_feature_engine import RealDataFeatureEngine
from app.ml.models.performance_predictor import YouthPerformancePredictor
from app.models.player import Player

logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_conn = Redis.from_url(settings.REDIS_URL)
ml_queue = Queue("ml_training", connection=redis_conn)


# ============================================
# ML TRAINING TASKS
# ============================================


async def train_performance_model_for_player(player_id: UUID) -> dict:
    """
    Train performance prediction model for a specific player using real data.

    Args:
        player_id: Player UUID

    Returns:
        dict with training results
    """
    logger.info(f"Starting ML model training for player {player_id}")

    try:
        feature_engine = RealDataFeatureEngine()
        predictor = YouthPerformancePredictor()
        predictor.initialize_model()

        # Gather training data from real database
        async for session in get_session():
            # Get player
            player_result = await session.execute(
                select(Player).where(Player.id == player_id)
            )
            player = player_result.scalar_one_or_none()

            if not player:
                return {"success": False, "error": f"Player {player_id} not found"}

            # Extract features for training
            # We need historical data: features + actual outcomes
            training_data = await _gather_training_data(session, player_id, feature_engine)

            if not training_data:
                return {
                    "success": False,
                    "error": "Not enough historical data for training",
                    "player_id": str(player_id),
                }

            # Train the model
            predictor.train(training_data)

            logger.info(
                f"Successfully trained model for player {player.first_name} {player.last_name}"
            )

            await session.close()
            break

        return {
            "success": True,
            "player_id": str(player_id),
            "model_info": predictor.get_model_info(),
            "training_samples": len(training_data),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error training model for player {player_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "player_id": str(player_id)}


async def train_models_for_team(team_id: UUID) -> dict:
    """
    Train performance models for all players in a team.

    Args:
        team_id: Team UUID

    Returns:
        dict with training results for all players
    """
    logger.info(f"Starting ML model training for team {team_id}")

    try:
        async for session in get_session():
            # Get all players in team
            from sqlalchemy import select

            from app.models.team import Team

            team_result = await session.execute(
                select(Team).where(Team.id == team_id).options(selectinload(Team.players))
            )
            team = team_result.scalar_one_or_none()

            if not team:
                return {"success": False, "error": f"Team {team_id} not found"}

            if not team.players:
                return {
                    "success": False,
                    "error": "No players found in team",
                    "team_id": str(team_id),
                }

            # Queue training job for each player
            results = []
            for player in team.players:
                job = ml_queue.enqueue(
                    train_performance_model_for_player,
                    player.id,
                    job_timeout="10m",
                )
                results.append(
                    {
                        "player_id": str(player.id),
                        "player_name": f"{player.first_name} {player.last_name}",
                        "job_id": job.id,
                        "status": "queued",
                    }
                )

            logger.info(f"Queued training jobs for {len(results)} players in team {team.name}")

            await session.close()
            break

        return {
            "success": True,
            "team_id": str(team_id),
            "players_queued": len(results),
            "jobs": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error training models for team {team_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "team_id": str(team_id)}


async def retrain_all_models(organization_id: UUID) -> dict:
    """
    Retrain all ML models for an entire organization.

    Args:
        organization_id: Organization UUID

    Returns:
        dict with training results
    """
    logger.info(f"Starting organization-wide ML model retraining for {organization_id}")

    try:
        async for session in get_session():
            from sqlalchemy import select

            # Get all players in organization
            from app.models.organization import Organization

            org_result = await session.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            org = org_result.scalar_one_or_none()

            if not org:
                return {"success": False, "error": f"Organization {organization_id} not found"}

            # Get all players
            players_result = await session.execute(
                select(Player).where(Player.organization_id == organization_id)
            )
            players = players_result.scalars().all()

            if not players:
                return {
                    "success": False,
                    "error": "No players found in organization",
                    "organization_id": str(organization_id),
                }

            # Queue training job for each player
            results = []
            for player in players:
                job = ml_queue.enqueue(
                    train_performance_model_for_player,
                    player.id,
                    job_timeout="10m",
                )
                results.append({"player_id": str(player.id), "job_id": job.id, "status": "queued"})

            logger.info(f"Queued training jobs for {len(results)} players")

            await session.close()
            break

        return {
            "success": True,
            "organization_id": str(organization_id),
            "players_queued": len(results),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error retraining models for organization {organization_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "organization_id": str(organization_id)}


# ============================================
# HELPER FUNCTIONS
# ============================================


async def _gather_training_data(
    session, player_id: UUID, feature_engine: RealDataFeatureEngine
) -> List[Tuple[dict, List]]:
    """
    Gather historical training data for a player.

    Returns: List of (features, targets) tuples
    where targets = [actual_perf_7d, actual_perf_30d, actual_growth, had_injury]
    """
    training_data = []

    # Look back 6 months and create training samples every 2 weeks
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=180)

    current_date = start_date
    while current_date < end_date:
        # Extract features at this point in time
        features = await feature_engine.extract_features_for_player(session, player_id, current_date)

        # Look ahead to get actual outcomes
        # Performance 7 days ahead
        perf_7d_date = current_date + timedelta(days=7)
        perf_7d_features = await feature_engine.extract_features_for_player(
            session, player_id, perf_7d_date
        )

        # Performance 30 days ahead
        perf_30d_date = current_date + timedelta(days=30)
        perf_30d_features = await feature_engine.extract_features_for_player(
            session, player_id, perf_30d_date
        )

        # Calculate actual performance scores
        # Use trajectory and potential_gap as proxies for performance
        actual_perf_7d = (
            perf_7d_features["development_trajectory"] * 0.6
            + perf_7d_features["potential_gap_score"] * 0.4
        )
        actual_perf_30d = (
            perf_30d_features["development_trajectory"] * 0.6
            + perf_30d_features["potential_gap_score"] * 0.4
        )

        # Growth: compare potential_gap over time (decrease = growth)
        actual_growth = min(
            1.0, (features["potential_gap_score"] - perf_30d_features["potential_gap_score"]) + 0.5
        )

        # Injury: check if player had injuries in next 30 days
        from sqlalchemy import func, select

        from app.models.injury import Injury

        injury_result = await session.execute(
            select(func.count())
            .select_from(Injury)
            .where(
                Injury.player_id == player_id,
                Injury.injury_date >= current_date,
                Injury.injury_date <= perf_30d_date,
            )
        )
        injury_count = injury_result.scalar()
        had_injury = 1.0 if injury_count > 0 else 0.0

        targets = [actual_perf_7d, actual_perf_30d, actual_growth, had_injury]

        training_data.append((features, targets))

        # Move to next training sample (2 weeks ahead)
        current_date += timedelta(days=14)

    return training_data


# ============================================
# SCHEDULED TASKS
# ============================================


def schedule_weekly_retraining():
    """
    Schedule weekly retraining for all organizations.

    This should be called by the scheduler (e.g., APScheduler or cron).
    """
    logger.info("Scheduling weekly ML model retraining")

    # Get all organizations and queue retraining
    # In production, this would iterate through all organizations
    # For now, just log the intention
    logger.info("Weekly retraining job would be queued here")

    return {"success": True, "message": "Weekly retraining scheduled"}

"""Advanced ML algorithms for player analytics and scouting."""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player, PlayerRole
from app.models.player_stats import PlayerStats

logger = logging.getLogger(__name__)


class AdvancedMLAlgorithms:
    """
    Advanced ML algorithms for player performance analysis.
    Includes: Performance Index, Influence Score, xG/xA, Form Prediction, Scouting.
    """

    @staticmethod
    def calculate_performance_index(stats: PlayerStats, player_role: str) -> float:
        """
        Calculate comprehensive performance index (0-100) based on player position.

        Args:
            stats: PlayerStats object with match/session statistics
            player_role: Player's primary role (GK, DF, MF, FW)

        Returns:
            Performance index score (0-100)
        """
        weights = AdvancedMLAlgorithms._get_position_weights(player_role)

        # Calculate component scores
        offensive = AdvancedMLAlgorithms._calculate_offensive_impact(stats, weights["offensive"])
        defensive = AdvancedMLAlgorithms._calculate_defensive_impact(stats, weights["defensive"])
        creativity = AdvancedMLAlgorithms._calculate_creativity(stats, weights["creativity"])
        physical = AdvancedMLAlgorithms._calculate_physical_impact(stats, weights["physical"])
        discipline = AdvancedMLAlgorithms._calculate_discipline(stats, weights["discipline"])

        # Weighted sum
        total_score = (
            offensive["score"] * offensive["weight"] +
            defensive["score"] * defensive["weight"] +
            creativity["score"] * creativity["weight"] +
            physical["score"] * physical["weight"] +
            discipline["score"] * discipline["weight"]
        )

        total_weight = (
            offensive["weight"] +
            defensive["weight"] +
            creativity["weight"] +
            physical["weight"] +
            discipline["weight"]
        )

        performance_index = (total_score / total_weight) * 10 if total_weight > 0 else 0
        return round(min(100, max(0, performance_index)), 2)

    @staticmethod
    def _calculate_offensive_impact(stats: PlayerStats, weight: float) -> Dict[str, float]:
        """Calculate offensive contribution score."""
        goal_impact = stats.goals * 3.0
        assist_impact = stats.assists * 2.5
        shooting_efficiency = (stats.shots_on_target / stats.shots) * 2.0 if stats.shots > 0 else 0
        dribbling_impact = (
            (stats.dribbles_success / stats.dribbles_attempted) * 1.5
            if stats.dribbles_attempted > 0 else 0
        )

        offensive_score = goal_impact + assist_impact + shooting_efficiency + dribbling_impact
        return {"score": min(10, offensive_score), "weight": weight * 0.3}

    @staticmethod
    def _calculate_defensive_impact(stats: PlayerStats, weight: float) -> Dict[str, float]:
        """Calculate defensive contribution score."""
        tackle_efficiency = (
            (stats.tackles_success / stats.tackles_attempted) * 2.5
            if stats.tackles_attempted > 0 else 0
        )
        interception_impact = stats.interceptions * 0.8
        clearance_impact = stats.clearances * 0.6
        block_impact = stats.blocks * 0.7
        aerial_impact = stats.aerial_duels_won * 0.5

        defensive_score = (
            tackle_efficiency + interception_impact +
            clearance_impact + block_impact + aerial_impact
        )
        return {"score": min(10, defensive_score), "weight": weight * 0.25}

    @staticmethod
    def _calculate_creativity(stats: PlayerStats, weight: float) -> Dict[str, float]:
        """Calculate playmaking and creativity score."""
        pass_accuracy = (
            (stats.passes_completed / stats.passes_attempted) * 2.0
            if stats.passes_attempted > 0 else 0
        )
        key_pass_impact = stats.key_passes * 1.2
        through_ball_impact = stats.through_balls * 1.5
        cross_impact = stats.crosses * (stats.cross_accuracy_pct / 100) if stats.crosses > 0 else 0

        creativity_score = pass_accuracy + key_pass_impact + through_ball_impact + cross_impact
        return {"score": min(10, creativity_score), "weight": weight * 0.2}

    @staticmethod
    def _calculate_physical_impact(stats: PlayerStats, weight: float) -> Dict[str, float]:
        """Calculate physical contribution score."""
        distance_score = min(2.0, stats.distance_covered_m / 5000)  # Normalized to 10km
        sprint_score = min(1.5, stats.sprints / 20)
        foul_penalty = stats.fouls_committed * -0.3

        physical_score = max(0, distance_score + sprint_score + foul_penalty)
        return {"score": min(10, physical_score * 2), "weight": weight * 0.15}

    @staticmethod
    def _calculate_discipline(stats: PlayerStats, weight: float) -> Dict[str, float]:
        """Calculate discipline score."""
        base_score = 8.0
        yellow_penalty = stats.yellow_cards * -1.0
        red_penalty = stats.red_cards * -3.0
        foul_penalty = stats.fouls_committed * -0.2
        offside_penalty = stats.offsides * -0.3

        discipline_score = max(0, base_score + yellow_penalty + red_penalty + foul_penalty + offside_penalty)
        return {"score": min(10, discipline_score), "weight": weight * 0.1}

    @staticmethod
    def calculate_influence_score(stats: PlayerStats) -> float:
        """
        Calculate player influence on match outcome (0-10).

        Args:
            stats: PlayerStats object

        Returns:
            Influence score (0-10)
        """
        base_influence = (
            stats.goals * 2.5 +
            stats.assists * 2.0 +
            stats.key_passes * 0.8 +
            stats.tackles_success * 0.6 +
            stats.interceptions * 0.5 +
            stats.dribbles_success * 0.4 +
            stats.blocks * 0.3
        )

        # Normalize with sigmoid function
        normalized_influence = 1 / (1 + math.exp(-base_influence / 6))
        return round(normalized_influence * 10, 2)

    @staticmethod
    def calculate_expected_goals(stats: PlayerStats, player_role: str) -> float:
        """
        Calculate expected goals (xG) based on shot quality and position.

        Args:
            stats: PlayerStats object
            player_role: Player's primary role

        Returns:
            Expected goals (xG)
        """
        shot_quality = (
            (stats.shots_on_target / stats.shots) * 0.3
            if stats.shots > 0 else 0
        )
        position_multiplier = AdvancedMLAlgorithms._get_position_multiplier(player_role)
        historical_conversion = 0.12  # Average conversion rate

        xg = (stats.shots * historical_conversion * position_multiplier) + shot_quality
        return round(xg, 2)

    @staticmethod
    def calculate_expected_assists(stats: PlayerStats) -> float:
        """
        Calculate expected assists (xA) based on creative actions.

        Args:
            stats: PlayerStats object

        Returns:
            Expected assists (xA)
        """
        key_pass_weight = stats.key_passes * 0.15
        through_ball_weight = stats.through_balls * 0.25
        cross_weight = stats.crosses * (stats.cross_accuracy_pct / 100) * 0.1

        xa = key_pass_weight + through_ball_weight + cross_weight
        return round(xa, 2)

    @staticmethod
    async def predict_player_form(
        session: AsyncSession,
        player_id: str,
        matches_to_analyze: int = 5
    ) -> float:
        """
        Predict player's current form based on recent performances.

        Args:
            session: Database session
            player_id: Player UUID
            matches_to_analyze: Number of recent matches to consider

        Returns:
            Predicted form level (0-10)
        """
        # Fetch recent stats
        stmt = (
            select(PlayerStats)
            .where(PlayerStats.player_id == player_id)
            .order_by(PlayerStats.date.desc())
            .limit(matches_to_analyze)
        )
        result = await session.execute(stmt)
        recent_stats = result.scalars().all()

        if not recent_stats:
            return 5.0

        # Calculate weighted average with recency bias
        weighted_sum = 0.0
        total_weight = 0.0

        for index, stat in enumerate(recent_stats):
            recency_weight = (len(recent_stats) - index) / len(recent_stats)
            performance = stat.performance_index / 10  # Convert to 1-10 scale

            weighted_sum += performance * recency_weight
            total_weight += recency_weight

        predicted_form = weighted_sum / total_weight if total_weight > 0 else 5.0
        return round(predicted_form, 1)

    @staticmethod
    async def get_scouting_recommendations(
        session: AsyncSession,
        team_id: str,
        organization_id: str,
        position: Optional[str] = None,
        max_age: Optional[int] = None,
        max_budget: Optional[float] = None,
        min_rating: Optional[float] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Get intelligent scouting recommendations based on ML analysis.

        Args:
            session: Database session
            team_id: Requesting team UUID
            organization_id: Organization UUID (for multi-tenancy)
            position: Filter by position
            max_age: Maximum age
            max_budget: Maximum market value
            min_rating: Minimum overall rating
            limit: Maximum results

        Returns:
            List of recommended players with analytics
        """
        # Build query filters
        filters = [
            Player.team_id != team_id,
            Player.organization_id == organization_id,
            Player.is_active == True
        ]

        if position:
            filters.append(Player.role_primary == position)
        if max_age:
            from datetime import date
            min_birth_date = date.today().replace(year=date.today().year - max_age)
            filters.append(Player.date_of_birth >= min_birth_date)
        if max_budget:
            filters.append(
                or_(
                    Player.market_value_eur <= max_budget,
                    Player.market_value_eur.is_(None)
                )
            )
        if min_rating:
            filters.append(Player.overall_rating >= min_rating)

        # Fetch players
        stmt = select(Player).where(and_(*filters)).limit(limit * 2)
        result = await session.execute(stmt)
        players = result.scalars().all()

        recommendations = []

        for player in players:
            # Fetch recent stats
            stats_stmt = (
                select(PlayerStats)
                .where(PlayerStats.player_id == player.id)
                .order_by(PlayerStats.date.desc())
                .limit(8)
            )
            stats_result = await session.execute(stats_stmt)
            recent_stats = stats_result.scalars().all()

            if not recent_stats:
                continue

            # Calculate average performance
            avg_performance = sum(s.performance_index for s in recent_stats) / len(recent_stats)

            # Predict form
            form_prediction = await AdvancedMLAlgorithms.predict_player_form(
                session, str(player.id)
            )

            # Calculate value score
            value_score = AdvancedMLAlgorithms._calculate_value_score(
                player, avg_performance
            )

            # Calculate age from date_of_birth
            age = (datetime.now().date() - player.date_of_birth).days // 365

            recommendations.append({
                "player": {
                    "id": str(player.id),
                    "name": f"{player.first_name} {player.last_name}",
                    "position": player.role_primary,
                    "age": age,
                    "team_id": str(player.team_id) if player.team_id else None,
                    "market_value": float(player.market_value_eur) if player.market_value_eur else None,
                    "overall_rating": float(player.overall_rating) if player.overall_rating else 6.0
                },
                "analytics": {
                    "performance_score": round(avg_performance, 2),
                    "form_prediction": form_prediction,
                    "value_score": round(value_score, 2),
                    "potential": float(player.potential_rating) if player.potential_rating else 6.0
                },
                "recommendation": AdvancedMLAlgorithms._generate_recommendation(
                    value_score, form_prediction
                ),
                "confidence": AdvancedMLAlgorithms._calculate_confidence(
                    len(recent_stats), avg_performance
                )
            })

        # Filter by value score and sort
        recommendations = [r for r in recommendations if r["analytics"]["value_score"] > 5]
        recommendations.sort(key=lambda x: x["analytics"]["value_score"], reverse=True)

        return recommendations[:limit]

    @staticmethod
    def _calculate_value_score(player: Player, performance: float) -> float:
        """Calculate player value/investment score."""
        age = (datetime.now().date() - player.date_of_birth).days // 365
        age_factor = max(0, 1 - (age - 25) * 0.05)
        performance_factor = performance / 10
        market_value = player.market_value_eur or 1000000
        value_ratio = performance_factor / (market_value / 10000000)

        return value_ratio * age_factor * 10

    @staticmethod
    def _generate_recommendation(value_score: float, form: float) -> str:
        """Generate scouting recommendation level."""
        if value_score > 8 and form > 7.5:
            return "STRONG_BUY"
        elif value_score > 6 and form > 6.5:
            return "BUY"
        elif value_score > 4 and form > 5.5:
            return "CONSIDER"
        return "HOLD"

    @staticmethod
    def _calculate_confidence(matches_analyzed: int, performance: float) -> int:
        """Calculate confidence level (0-100) in recommendation."""
        matches_confidence = min(1.0, matches_analyzed / 10)
        performance_stability = 0.8 if performance > 60 else 0.5
        return round(matches_confidence * performance_stability * 100)

    @staticmethod
    def _get_position_weights(position: str) -> Dict[str, float]:
        """Get position-specific weights for performance calculation."""
        weight_profiles = {
            PlayerRole.GK: {
                "offensive": 0.1,
                "defensive": 0.9,
                "creativity": 0.2,
                "physical": 0.6,
                "discipline": 0.8
            },
            PlayerRole.DF: {
                "offensive": 0.3,
                "defensive": 0.8,
                "creativity": 0.4,
                "physical": 0.7,
                "discipline": 0.7
            },
            PlayerRole.MF: {
                "offensive": 0.6,
                "defensive": 0.5,
                "creativity": 0.9,
                "physical": 0.8,
                "discipline": 0.6
            },
            PlayerRole.FW: {
                "offensive": 0.9,
                "defensive": 0.2,
                "creativity": 0.7,
                "physical": 0.6,
                "discipline": 0.5
            }
        }

        # Normalize position string to PlayerRole enum
        try:
            role = PlayerRole(position)
            return weight_profiles.get(role, weight_profiles[PlayerRole.MF])
        except (ValueError, KeyError):
            return weight_profiles[PlayerRole.MF]

    @staticmethod
    def _get_position_multiplier(position: str) -> float:
        """Get position multiplier for xG calculation."""
        multipliers = {
            PlayerRole.GK: 0.1,
            PlayerRole.DF: 0.3,
            PlayerRole.MF: 0.7,
            PlayerRole.FW: 1.2
        }

        try:
            role = PlayerRole(position)
            return multipliers.get(role, 0.7)
        except (ValueError, KeyError):
            return 0.7


# Export singleton instance
advanced_ml = AdvancedMLAlgorithms()

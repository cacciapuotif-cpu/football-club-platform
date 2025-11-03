"""
Real Feature Engine - Extract ML features from real database data.
NO SYNTHETIC DATA - Only real player metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.injury import Injury
from app.models.match import Attendance, Match
from app.models.performance import PhysicalTest
from app.models.player import Player
from app.models.session import TrainingSession
from app.models.wellness import WellnessData

logger = logging.getLogger(__name__)


class RealDataFeatureEngine:
    """
    Feature engineering from REAL DATABASE DATA ONLY.

    Extracts youth-specific features for ML models:
    - biological_age_factor
    - load_tolerance_ratio
    - skill_acquisition_rate
    - decision_making_velocity
    - pressure_performance_ratio
    - mental_fatigue_resistance
    - potential_gap_score
    - development_trajectory
    """

    def __init__(self):
        self.lookback_days = 90  # Analyze last 90 days of data

    async def extract_features_for_player(
        self,
        session: AsyncSession,
        player_id: UUID,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Extract all features for a player using ONLY real database data.

        Args:
            session: Database session
            player_id: Player UUID
            reference_date: Date to compute features from (default: now)

        Returns:
            Dictionary of features with values 0.0-1.0
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        lookback_start = reference_date - timedelta(days=self.lookback_days)

        try:
            # Get player info
            player = await self._get_player(session, player_id)
            if not player:
                logger.warning(f"Player {player_id} not found, returning default features")
                return self._get_default_features()

            # Extract each feature from real data
            features = {
                "biological_age_factor": await self._calculate_biological_age_factor(
                    session, player, reference_date
                ),
                "load_tolerance_ratio": await self._calculate_load_tolerance(
                    session, player_id, lookback_start, reference_date
                ),
                "skill_acquisition_rate": await self._calculate_skill_acquisition(
                    session, player_id, lookback_start, reference_date
                ),
                "decision_making_velocity": await self._calculate_decision_making(
                    session, player_id, lookback_start, reference_date
                ),
                "pressure_performance_ratio": await self._calculate_pressure_performance(
                    session, player_id, lookback_start, reference_date
                ),
                "mental_fatigue_resistance": await self._calculate_mental_fatigue_resistance(
                    session, player_id, lookback_start, reference_date
                ),
                "potential_gap_score": await self._calculate_potential_gap(
                    session, player_id, lookback_start, reference_date
                ),
                "development_trajectory": await self._calculate_development_trajectory(
                    session, player_id, lookback_start, reference_date
                ),
            }

            logger.info(f"Extracted features for player {player_id} from REAL data")
            return features

        except Exception as e:
            logger.error(f"Error extracting features for player {player_id}: {e}", exc_info=True)
            return self._get_default_features()

    async def _get_player(self, session: AsyncSession, player_id: UUID) -> Optional[Player]:
        """Get player from database."""
        result = await session.execute(select(Player).where(Player.id == player_id))
        return result.scalar_one_or_none()

    async def _calculate_biological_age_factor(
        self, session: AsyncSession, player: Player, reference_date: datetime
    ) -> float:
        """
        Calculate biological age factor from player's actual age and development.

        Returns: 0.8-1.2 (1.0 = on track, >1.0 = advanced, <1.0 = delayed)
        """
        if not player.date_of_birth:
            return 1.0  # Neutral if no DOB

        # Calculate actual age
        age_years = (reference_date.date() - player.date_of_birth).days / 365.25

        # Youth players typically 14-21
        if age_years < 14:
            return 0.8  # Young for youth system
        elif age_years > 21:
            return 1.2  # Mature for youth system
        else:
            # Normalize to 0.8-1.2 based on age distribution
            normalized = 0.8 + ((age_years - 14) / 7) * 0.4
            return round(normalized, 3)

    async def _calculate_load_tolerance(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate load tolerance ratio from training sessions and wellness data.

        Returns: 0.0-1.0 (higher = better tolerance, lower = near overload)
        """
        # Get training sessions
        sessions_result = await session.execute(
            select(TrainingSession)
            .where(
                TrainingSession.player_id == player_id,
                TrainingSession.created_at >= start_date,
                TrainingSession.created_at <= end_date,
            )
            .order_by(TrainingSession.created_at.desc())
        )
        sessions = sessions_result.scalars().all()

        if not sessions:
            return 0.5  # Neutral if no data

        # Calculate average RPE (Rate of Perceived Exertion)
        avg_rpe = sum(s.rpe for s in sessions if s.rpe) / len([s for s in sessions if s.rpe])

        # Get wellness data for same period
        wellness_result = await session.execute(
            select(WellnessData)
            .where(
                WellnessData.player_id == player_id,
                WellnessData.created_at >= start_date,
                WellnessData.created_at <= end_date,
            )
        )
        wellness_data = wellness_result.scalars().all()

        if not wellness_data:
            # Use RPE only
            # RPE 1-10 scale: normalize to 0-1 (inverted: high RPE = low tolerance)
            tolerance = 1.0 - (avg_rpe / 10.0)
            return max(0.0, min(1.0, tolerance))

        # Calculate average fatigue (1-5 scale, lower is better)
        avg_fatigue = sum(w.fatigue for w in wellness_data if w.fatigue) / len(
            [w for w in wellness_data if w.fatigue]
        )

        # Combine RPE and fatigue
        # High RPE + High fatigue = Low tolerance
        rpe_normalized = avg_rpe / 10.0  # 0-1
        fatigue_normalized = avg_fatigue / 5.0  # 0-1

        tolerance = 1.0 - ((rpe_normalized + fatigue_normalized) / 2)

        return max(0.0, min(1.0, round(tolerance, 3)))

    async def _calculate_skill_acquisition(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate skill acquisition rate from physical test improvements.

        Returns: 0.0-1.0 (higher = faster learning)
        """
        # Get physical tests ordered by date
        tests_result = await session.execute(
            select(PhysicalTest)
            .where(
                PhysicalTest.player_id == player_id,
                PhysicalTest.created_at >= start_date,
                PhysicalTest.created_at <= end_date,
            )
            .order_by(PhysicalTest.created_at.asc())
        )
        tests = tests_result.scalars().all()

        if len(tests) < 2:
            return 0.5  # Neutral if not enough data

        # Calculate improvement rate across tests
        improvements = []

        # Check various metrics for improvement
        metrics = ["sprint_30m", "agility_t_test", "vertical_jump_cm", "endurance_yoyo_level"]

        for metric in metrics:
            values = [getattr(test, metric) for test in tests if getattr(test, metric, None)]
            if len(values) >= 2:
                # Calculate percentage improvement from first to last
                first, last = values[0], values[-1]
                if first > 0:
                    improvement_pct = ((last - first) / first) * 100
                    improvements.append(improvement_pct)

        if not improvements:
            return 0.5  # Neutral if no metrics to compare

        # Average improvement rate
        avg_improvement = sum(improvements) / len(improvements)

        # Normalize: 0% = 0.5, +10% = 0.8, +20% = 1.0, -10% = 0.2
        if avg_improvement >= 0:
            rate = 0.5 + min(0.5, avg_improvement / 40)  # Cap at 1.0
        else:
            rate = 0.5 + max(-0.3, avg_improvement / 40)  # Floor at 0.2

        return max(0.0, min(1.0, round(rate, 3)))

    async def _calculate_decision_making(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate decision making from match performance (assists, ratings).

        Returns: 0.0-1.0 (higher = better decision making)
        """
        # Get match attendances
        attendance_result = await session.execute(
            select(Attendance)
            .join(Match, Attendance.match_id == Match.id)
            .where(
                Attendance.player_id == player_id,
                Match.match_date >= start_date,
                Match.match_date <= end_date,
            )
        )
        attendances = attendance_result.scalars().all()

        if not attendances:
            return 0.5  # Neutral if no match data

        # Decision making indicators:
        # 1. Assists per match
        # 2. Coach rating
        # 3. Analyst rating

        total_assists = sum(a.assists for a in attendances)
        total_matches = len(attendances)
        assists_per_match = total_assists / total_matches if total_matches > 0 else 0

        # Get average ratings
        coach_ratings = [a.coach_rating for a in attendances if a.coach_rating]
        analyst_ratings = [a.analyst_rating for a in attendances if a.analyst_rating]

        avg_coach_rating = sum(coach_ratings) / len(coach_ratings) if coach_ratings else 6.0
        avg_analyst_rating = sum(analyst_ratings) / len(analyst_ratings) if analyst_ratings else 6.0

        # Combine indicators
        # Assists: 0.5+ per match = excellent (0.3 weight)
        assists_score = min(1.0, assists_per_match / 0.5)

        # Ratings: 7.5+ / 10 = excellent (0.7 weight)
        avg_rating = (avg_coach_rating + avg_analyst_rating) / 2
        ratings_score = (avg_rating - 5.0) / 5.0  # Normalize 5-10 to 0-1

        decision_making = (assists_score * 0.3) + (ratings_score * 0.7)

        return max(0.0, min(1.0, round(decision_making, 3)))

    async def _calculate_pressure_performance(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate performance under pressure from important matches.

        Returns: 0.0-1.0 (higher = better under pressure)
        """
        # Get match attendances
        attendance_result = await session.execute(
            select(Attendance, Match)
            .join(Match, Attendance.match_id == Match.id)
            .where(
                Attendance.player_id == player_id,
                Match.match_date >= start_date,
                Match.match_date <= end_date,
            )
        )
        matches_data = attendance_result.all()

        if not matches_data:
            return 0.5  # Neutral if no match data

        # Identify "pressure" matches (competitive matches vs friendly)
        pressure_performances = []
        regular_performances = []

        for attendance, match in matches_data:
            avg_rating = 0
            rating_count = 0

            if attendance.coach_rating:
                avg_rating += attendance.coach_rating
                rating_count += 1
            if attendance.analyst_rating:
                avg_rating += attendance.analyst_rating
                rating_count += 1

            if rating_count > 0:
                avg_rating = avg_rating / rating_count

                # Pressure matches: LEAGUE, CUP (not FRIENDLY, TRAINING_MATCH)
                if match.match_type.value in ["LEAGUE", "CUP"]:
                    pressure_performances.append(avg_rating)
                else:
                    regular_performances.append(avg_rating)

        if not pressure_performances and not regular_performances:
            return 0.5  # No ratings available

        # Calculate ratio of pressure vs regular performance
        if pressure_performances and regular_performances:
            avg_pressure = sum(pressure_performances) / len(pressure_performances)
            avg_regular = sum(regular_performances) / len(regular_performances)

            if avg_regular > 0:
                ratio = avg_pressure / avg_regular  # >1.0 = better under pressure
                # Normalize: 0.8 = 0.3, 1.0 = 0.5, 1.2 = 0.8, 1.4+ = 1.0
                score = 0.5 + ((ratio - 1.0) * 2.5)
                return max(0.0, min(1.0, round(score, 3)))

        # If only one type available, use absolute performance
        all_perf = pressure_performances + regular_performances
        avg_perf = sum(all_perf) / len(all_perf)
        score = (avg_perf - 5.0) / 5.0  # Normalize 5-10 to 0-1
        return max(0.0, min(1.0, round(score, 3)))

    async def _calculate_mental_fatigue_resistance(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate mental fatigue resistance from wellness data trends.

        Returns: 0.0-1.0 (higher = better resistance)
        """
        # Get wellness data
        wellness_result = await session.execute(
            select(WellnessData)
            .where(
                WellnessData.player_id == player_id,
                WellnessData.created_at >= start_date,
                WellnessData.created_at <= end_date,
            )
            .order_by(WellnessData.created_at.asc())
        )
        wellness_data = wellness_result.scalars().all()

        if len(wellness_data) < 5:
            return 0.5  # Neutral if not enough data

        # Mental fatigue indicators:
        # 1. Mood stability (less variation = better)
        # 2. Sleep quality consistency
        # 3. Stress levels

        moods = [w.mood for w in wellness_data if w.mood]
        sleeps = [w.sleep_hours for w in wellness_data if w.sleep_hours]
        stress_levels = [w.stress for w in wellness_data if w.stress]

        resistance_score = 0.0
        components = 0

        # Mood stability (1-5 scale, higher is better)
        if len(moods) >= 5:
            avg_mood = sum(moods) / len(moods)
            mood_variance = sum((m - avg_mood) ** 2 for m in moods) / len(moods)

            # High mood + Low variance = Good mental state
            mood_score = (avg_mood / 5.0) * 0.7 + (1 - min(1, mood_variance / 2)) * 0.3
            resistance_score += mood_score
            components += 1

        # Sleep consistency (7-9 hours is optimal)
        if len(sleeps) >= 5:
            avg_sleep = sum(sleeps) / len(sleeps)
            # Optimal sleep: 7.5-8.5 hours = 1.0
            if 7.5 <= avg_sleep <= 8.5:
                sleep_score = 1.0
            elif avg_sleep < 7.5:
                sleep_score = max(0.3, avg_sleep / 7.5)
            else:
                sleep_score = max(0.3, 1.0 - ((avg_sleep - 8.5) / 3))

            resistance_score += sleep_score
            components += 1

        # Stress levels (1-5 scale, lower is better)
        if len(stress_levels) >= 5:
            avg_stress = sum(stress_levels) / len(stress_levels)
            stress_score = 1.0 - (avg_stress / 5.0)
            resistance_score += stress_score
            components += 1

        if components == 0:
            return 0.5

        final_score = resistance_score / components
        return max(0.0, min(1.0, round(final_score, 3)))

    async def _calculate_potential_gap(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate potential gap score (current vs potential performance).

        Returns: 0.0-1.0 (lower = more room to grow, higher = near potential)
        """
        # Get physical tests and match performance
        tests_result = await session.execute(
            select(PhysicalTest)
            .where(
                PhysicalTest.player_id == player_id,
                PhysicalTest.created_at >= start_date,
                PhysicalTest.created_at <= end_date,
            )
        )
        tests = tests_result.scalars().all()

        attendance_result = await session.execute(
            select(Attendance)
            .join(Match, Attendance.match_id == Match.id)
            .where(
                Attendance.player_id == player_id,
                Match.match_date >= start_date,
                Match.match_date <= end_date,
            )
        )
        attendances = attendance_result.scalars().all()

        if not tests and not attendances:
            return 0.7  # Assume room for growth if no data

        # Calculate current performance level
        performance_indicators = []

        # Physical tests: Compare to youth benchmarks
        if tests:
            latest_test = tests[-1]  # Most recent

            # Sprint benchmark: <4.5s = 1.0, >5.5s = 0.3
            if latest_test.sprint_30m:
                sprint_score = max(0.3, min(1.0, (5.5 - latest_test.sprint_30m) / 1.0))
                performance_indicators.append(sprint_score)

            # Vertical jump benchmark: >60cm = 1.0, <40cm = 0.3
            if latest_test.vertical_jump_cm:
                jump_score = max(0.3, min(1.0, (latest_test.vertical_jump_cm - 40) / 20))
                performance_indicators.append(jump_score)

        # Match performance: ratings
        if attendances:
            coach_ratings = [a.coach_rating for a in attendances if a.coach_rating]
            if coach_ratings:
                avg_rating = sum(coach_ratings) / len(coach_ratings)
                rating_score = (avg_rating - 5.0) / 5.0  # 5-10 normalized to 0-1
                performance_indicators.append(max(0.0, min(1.0, rating_score)))

        if not performance_indicators:
            return 0.7  # Default assumption

        # Average current performance
        current_level = sum(performance_indicators) / len(performance_indicators)

        # Potential gap: inverse of current level
        # High current = 0.9+ (near potential)
        # Low current = 0.3- (lots of room to grow)
        # We return current_level directly as the gap score

        return max(0.0, min(1.0, round(current_level, 3)))

    async def _calculate_development_trajectory(
        self, session: AsyncSession, player_id: UUID, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Calculate development trajectory (improvement trend).

        Returns: 0.0-1.0 (higher = positive trajectory)
        """
        # Get training sessions over time
        sessions_result = await session.execute(
            select(TrainingSession)
            .where(
                TrainingSession.player_id == player_id,
                TrainingSession.created_at >= start_date,
                TrainingSession.created_at <= end_date,
            )
            .order_by(TrainingSession.created_at.asc())
        )
        sessions = sessions_result.scalars().all()

        # Get physical tests over time
        tests_result = await session.execute(
            select(PhysicalTest)
            .where(
                PhysicalTest.player_id == player_id,
                PhysicalTest.created_at >= start_date,
                PhysicalTest.created_at <= end_date,
            )
            .order_by(PhysicalTest.created_at.asc())
        )
        tests = tests_result.scalars().all()

        if len(tests) < 2:
            # Use training frequency as proxy
            if len(sessions) >= 10:
                # Consistent training = positive trajectory
                weeks = (end_date - start_date).days / 7
                sessions_per_week = len(sessions) / weeks if weeks > 0 else 0
                # 3+ sessions/week = 0.7, 5+ = 0.9
                trajectory = min(0.9, 0.5 + (sessions_per_week / 10))
                return round(trajectory, 3)
            return 0.6  # Neutral

        # Calculate physical improvement trend
        improvements = []

        # Compare first half vs second half of period
        mid_point = len(tests) // 2
        first_half = tests[:mid_point]
        second_half = tests[mid_point:]

        metrics = ["sprint_30m", "vertical_jump_cm", "endurance_yoyo_level"]

        for metric in metrics:
            first_values = [getattr(t, metric) for t in first_half if getattr(t, metric, None)]
            second_values = [getattr(t, metric) for t in second_half if getattr(t, metric, None)]

            if first_values and second_values:
                avg_first = sum(first_values) / len(first_values)
                avg_second = sum(second_values) / len(second_values)

                if avg_first > 0:
                    improvement = ((avg_second - avg_first) / avg_first) * 100
                    improvements.append(improvement)

        if not improvements:
            return 0.6  # Neutral

        avg_improvement = sum(improvements) / len(improvements)

        # Normalize: +5% = 0.7, +10% = 0.8, +15%+ = 0.9+
        if avg_improvement >= 0:
            trajectory = 0.6 + min(0.4, avg_improvement / 40)
        else:
            trajectory = 0.6 + max(-0.4, avg_improvement / 40)

        return max(0.0, min(1.0, round(trajectory, 3)))

    def _get_default_features(self) -> Dict[str, float]:
        """Return neutral default features when no data available."""
        return {
            "biological_age_factor": 1.0,
            "load_tolerance_ratio": 0.5,
            "skill_acquisition_rate": 0.5,
            "decision_making_velocity": 0.5,
            "pressure_performance_ratio": 0.5,
            "mental_fatigue_resistance": 0.5,
            "potential_gap_score": 0.7,
            "development_trajectory": 0.6,
        }

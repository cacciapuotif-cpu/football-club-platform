"""Readiness score calculator with ML-based predictions."""

from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.test import WellnessData


class ReadinessCalculator:
    """Calculate daily readiness score from wellness and workload metrics."""

    @staticmethod
    def normalize_score(value: float, optimal: float, range_low: float, range_high: float) -> float:
        """
        Normalize a metric to 0-100 score.

        Args:
            value: Current value
            optimal: Optimal value (gets score 100)
            range_low: Lower boundary (gets score 0)
            range_high: Upper boundary (gets score 0)

        Returns:
            Score 0-100
        """
        if value == optimal:
            return 100.0

        if value < optimal:
            # Between range_low and optimal
            if value <= range_low:
                return 0.0
            return ((value - range_low) / (optimal - range_low)) * 100.0
        else:
            # Between optimal and range_high
            if value >= range_high:
                return 0.0
            return ((range_high - value) / (range_high - optimal)) * 100.0

    @staticmethod
    def calculate_sleep_score(sleep_hours: Optional[float], sleep_quality: Optional[int]) -> float:
        """
        Calculate sleep score (0-100).

        Optimal: 8 hours, quality 5/5
        """
        if sleep_hours is None and sleep_quality is None:
            return 50.0  # Neutral if no data

        hours_score = 100.0
        if sleep_hours is not None:
            # Optimal: 8h, range 4-12h
            hours_score = ReadinessCalculator.normalize_score(sleep_hours, optimal=8.0, range_low=4.0, range_high=12.0)

        quality_score = 100.0
        if sleep_quality is not None:
            # Linear 1-5 to 0-100
            quality_score = ((sleep_quality - 1) / 4) * 100

        # Weighted average: hours 60%, quality 40%
        return 0.6 * hours_score + 0.4 * quality_score

    @staticmethod
    def calculate_hrv_score(hrv_ms: Optional[float], resting_hr_bpm: Optional[int]) -> float:
        """
        Calculate HRV/HR score (0-100).

        Higher HRV = better (optimal 70+)
        Lower resting HR = better (optimal 50-60)
        """
        if hrv_ms is None and resting_hr_bpm is None:
            return 50.0

        hrv_component = 100.0
        if hrv_ms is not None:
            # Optimal: 70, range 20-120
            hrv_component = ReadinessCalculator.normalize_score(hrv_ms, optimal=70.0, range_low=20.0, range_high=120.0)

        hr_component = 100.0
        if resting_hr_bpm is not None:
            # Optimal: 55, range 40-90
            hr_component = ReadinessCalculator.normalize_score(resting_hr_bpm, optimal=55.0, range_low=40.0, range_high=90.0)

        # Equal weight
        return 0.5 * hrv_component + 0.5 * hr_component

    @staticmethod
    def calculate_recovery_score(doms_rating: Optional[int], fatigue_rating: Optional[int]) -> float:
        """
        Calculate recovery score (0-100).

        Lower DOMS/fatigue = better recovery
        """
        if doms_rating is None and fatigue_rating is None:
            return 50.0

        doms_score = 100.0
        if doms_rating is not None:
            # 1 = 100, 5 = 0
            doms_score = ((5 - doms_rating) / 4) * 100

        fatigue_score = 100.0
        if fatigue_rating is not None:
            # 1 = 100, 5 = 0
            fatigue_score = ((5 - fatigue_rating) / 4) * 100

        # Equal weight
        return 0.5 * doms_score + 0.5 * fatigue_score

    @staticmethod
    def calculate_wellness_score(stress_rating: Optional[int], mood_rating: Optional[int]) -> float:
        """
        Calculate wellness score (0-100).

        Lower stress, higher mood = better
        """
        if stress_rating is None and mood_rating is None:
            return 50.0

        stress_score = 100.0
        if stress_rating is not None:
            # 1 = 100, 5 = 0
            stress_score = ((5 - stress_rating) / 4) * 100

        mood_score = 100.0
        if mood_rating is not None:
            # 1 = 0, 10 = 100
            mood_score = ((mood_rating - 1) / 9) * 100

        # Equal weight
        return 0.5 * stress_score + 0.5 * mood_score

    @staticmethod
    def calculate_workload_score(acute_chronic_ratio: Optional[float]) -> float:
        """
        Calculate workload score (0-100).

        Optimal ACWR: 0.8-1.3
        """
        if acute_chronic_ratio is None:
            return 100.0  # Assume OK if no data

        acwr = acute_chronic_ratio

        # Optimal range 0.8-1.3
        if 0.8 <= acwr <= 1.3:
            return 100.0
        elif acwr < 0.8:
            # Under-training (0.5 = 50, 0 = 0)
            return max(0, (acwr / 0.8) * 100)
        else:
            # Over-training (1.3 = 100, 2.0 = 0)
            return max(0, ((2.0 - acwr) / 0.7) * 100)

    @staticmethod
    def calculate_overall_readiness(
        sleep_score: float,
        hrv_score: float,
        recovery_score: float,
        wellness_score: float,
        workload_score: float
    ) -> float:
        """
        Calculate overall readiness score as weighted average.

        Weights:
        - Sleep: 25%
        - HRV/HR: 25%
        - Recovery: 20%
        - Wellness: 15%
        - Workload: 15%
        """
        readiness = (
            0.25 * sleep_score +
            0.25 * hrv_score +
            0.20 * recovery_score +
            0.15 * wellness_score +
            0.15 * workload_score
        )
        return round(readiness, 1)

    @staticmethod
    def get_training_intensity_recommendation(readiness_score: float) -> str:
        """
        Recommend training intensity based on readiness score.

        Returns: LOW, MODERATE, HIGH, MAX
        """
        if readiness_score >= 80:
            return "MAX"
        elif readiness_score >= 65:
            return "HIGH"
        elif readiness_score >= 50:
            return "MODERATE"
        else:
            return "LOW"

    @staticmethod
    def check_injury_risk_flag(readiness_score: float, recovery_score: float, workload_score: float) -> bool:
        """
        Flag injury risk if readiness is low and recovery/workload are concerning.
        """
        if readiness_score < 40:
            return True
        if recovery_score < 30 and workload_score < 50:
            return True
        return False

    @staticmethod
    async def calculate_acwr(
        player_id,
        organization_id,
        target_date: date,
        session: AsyncSession
    ) -> Optional[float]:
        """
        Calculate Acute:Chronic Workload Ratio.

        Acute: last 7 days
        Chronic: last 28 days
        """
        chronic_start = target_date - timedelta(days=28)

        query = select(WellnessData).where(
            WellnessData.player_id == player_id,
            WellnessData.organization_id == organization_id,
            WellnessData.date >= chronic_start,
            WellnessData.date < target_date,
            WellnessData.training_load.isnot(None)
        ).order_by(WellnessData.date)

        result = await session.execute(query)
        wellness_list = result.scalars().all()

        if len(wellness_list) < 7:
            return None  # Not enough data

        # Get last 7 and last 28 days loads
        recent_7 = [w for w in wellness_list if (target_date - w.date).days <= 7]
        all_28 = wellness_list

        acute_load = sum(w.training_load for w in recent_7 if w.training_load)
        chronic_load = sum(w.training_load for w in all_28 if w.training_load)

        if chronic_load == 0:
            return None

        return round(acute_load / chronic_load, 2)


async def calculate_readiness_score(
    player_id,
    organization_id,
    target_date: date,
    wellness_data: Dict,
    session: AsyncSession
) -> Dict:
    """
    Calculate full readiness score with all components.

    Args:
        player_id: Player UUID
        organization_id: Organization UUID
        target_date: Date to calculate for
        wellness_data: Dict with wellness metrics
        session: Database session

    Returns:
        Dict with all readiness components and recommendations
    """
    calc = ReadinessCalculator()

    # Calculate component scores
    sleep_score = calc.calculate_sleep_score(
        wellness_data.get("sleep_hours"),
        wellness_data.get("sleep_quality")
    )

    hrv_score = calc.calculate_hrv_score(
        wellness_data.get("hrv_ms"),
        wellness_data.get("resting_hr_bpm")
    )

    recovery_score = calc.calculate_recovery_score(
        wellness_data.get("doms_rating"),
        wellness_data.get("fatigue_rating")
    )

    wellness_score = calc.calculate_wellness_score(
        wellness_data.get("stress_rating"),
        wellness_data.get("mood_rating")
    )

    # Calculate ACWR
    acwr = await calc.calculate_acwr(player_id, organization_id, target_date, session)
    workload_score = calc.calculate_workload_score(acwr)

    # Overall readiness
    readiness_score = calc.calculate_overall_readiness(
        sleep_score, hrv_score, recovery_score, wellness_score, workload_score
    )

    # Recommendations
    recommended_intensity = calc.get_training_intensity_recommendation(readiness_score)
    can_train_full = readiness_score >= 60
    injury_risk_flag = calc.check_injury_risk_flag(readiness_score, recovery_score, workload_score)

    return {
        "readiness_score": readiness_score,
        "sleep_score": round(sleep_score, 1),
        "hrv_score": round(hrv_score, 1),
        "recovery_score": round(recovery_score, 1),
        "wellness_score": round(wellness_score, 1),
        "workload_score": round(workload_score, 1),
        "acute_chronic_ratio": acwr,
        "yesterday_training_load": wellness_data.get("training_load"),
        "recommended_training_intensity": recommended_intensity,
        "can_train_full": can_train_full,
        "injury_risk_flag": injury_risk_flag,
        "predicted_performance_today": None,  # TODO: ML model
        "injury_risk_probability": None,  # TODO: ML model
    }

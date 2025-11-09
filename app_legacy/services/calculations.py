"""Service for calculating derived metrics and performance indices."""
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics

from app.models.models import (
    MetricsPhysical, MetricsTechnical, AnalyticsOutputs,
    Session as SessionModel
)


def calculate_bmi(height_cm: Optional[Decimal], weight_kg: Optional[Decimal]) -> Optional[Decimal]:
    """
    Calculate BMI from height and weight.
    BMI = weight_kg / (height_cm/100)^2
    """
    if not height_cm or not weight_kg or height_cm <= 0:
        return None

    height_m = height_cm / Decimal("100")
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 2)


def calculate_pass_accuracy(completed: int, attempted: int) -> Optional[Decimal]:
    """
    Calculate pass accuracy percentage.
    pass_accuracy_pct = (passes_completed / passes_attempted) * 100
    """
    if attempted == 0:
        return None
    return round(Decimal(completed) / Decimal(attempted) * Decimal("100"), 2)


def calculate_shot_accuracy(on_target: int, shots: int) -> Optional[Decimal]:
    """
    Calculate shot accuracy percentage.
    shot_accuracy_pct = (shots_on_target / shots) * 100
    """
    if shots == 0:
        return None
    return round(Decimal(on_target) / Decimal(shots) * Decimal("100"), 2)


def calculate_dribble_success(successful: int, failed: int) -> Optional[Decimal]:
    """
    Calculate dribble success percentage.
    dribble_success_pct = successful_dribbles / (successful_dribbles + failed_dribbles) * 100
    """
    total = successful + failed
    if total == 0:
        return None
    return round(Decimal(successful) / Decimal(total) * Decimal("100"), 2)


def calculate_performance_index(
    pass_accuracy_pct: Optional[Decimal],
    progressive_passes: int,
    interceptions: int,
    successful_dribbles: int,
    sprints_over_25kmh: int,
    resting_hr_bpm: int,
    yoyo_level: Optional[Decimal],
    distance_km: Decimal,
    sleep_hours: Optional[Decimal],
    coach_rating: Optional[Decimal],
    rpe: Decimal
) -> Decimal:
    """
    Calculate performance index (0-100) with weights for midfielder.

    Formula (per centrocampista):
    - 0.12 * pass_accuracy_pct
    - 0.35 * (progressive_passes + 0.6*interceptions + 0.8*successful_dribbles)
    - 0.10 * sprints_over_25kmh
    - 0.10 * (12 - (resting_hr_bpm - 50)/2) (lower HR is better)
    - 0.08 * yoyo_level
    - 0.10 * distance_km
    - 0.05 * sleep_hours
    - 0.05 * coach_rating (if available)
    - -0.05 * |rpe - 7|

    Clamped to 40-95 range, then normalized to 0-100
    """
    score = Decimal("0")

    # Pass accuracy component (0.12 weight)
    if pass_accuracy_pct is not None:
        score += Decimal("0.12") * pass_accuracy_pct

    # Tactical actions component (0.35 weight)
    tactical_score = (
        progressive_passes +
        Decimal("0.6") * interceptions +
        Decimal("0.8") * successful_dribbles
    )
    score += Decimal("0.35") * tactical_score

    # Sprints component (0.10 weight)
    score += Decimal("0.10") * sprints_over_25kmh

    # Heart rate component (0.10 weight) - lower is better
    hr_component = Decimal("12") - (Decimal(resting_hr_bpm) - Decimal("50")) / Decimal("2")
    hr_component = max(Decimal("0"), hr_component)  # Floor at 0
    score += Decimal("0.10") * hr_component

    # Yo-yo level component (0.08 weight)
    if yoyo_level is not None:
        score += Decimal("0.08") * yoyo_level

    # Distance component (0.10 weight)
    score += Decimal("0.10") * distance_km

    # Sleep component (0.05 weight)
    if sleep_hours is not None:
        score += Decimal("0.05") * sleep_hours

    # Coach rating component (0.05 weight)
    if coach_rating is not None:
        score += Decimal("0.05") * coach_rating

    # RPE penalty component (-0.05 weight) - optimal RPE is 7
    rpe_penalty = abs(rpe - Decimal("7"))
    score -= Decimal("0.05") * rpe_penalty

    # Clamp to 40-95 range
    score = max(Decimal("40"), min(Decimal("95"), score))

    # Normalize to 0-100 scale
    # (score - 40) / (95 - 40) * 100
    normalized = ((score - Decimal("40")) / Decimal("55")) * Decimal("100")

    return round(normalized, 2)


def calculate_rolling_average(
    db: Session,
    player_id: str,
    current_session_id: str,
    window: int = 4
) -> Optional[Decimal]:
    """
    Calculate rolling average of performance_index for last N sessions.

    Args:
        db: Database session
        player_id: Player UUID
        current_session_id: Current session UUID
        window: Number of sessions to include in rolling average (default 4)

    Returns:
        Rolling average or None if insufficient data
    """
    # Get last N performance indices for this player, including current
    results = db.query(AnalyticsOutputs.performance_index).join(
        SessionModel
    ).filter(
        SessionModel.player_id == player_id
    ).order_by(
        SessionModel.session_date.desc()
    ).limit(window).all()

    if not results or len(results) < 2:  # Need at least 2 sessions for rolling avg
        return None

    indices = [float(r[0]) for r in results]
    avg = statistics.mean(indices)

    return round(Decimal(str(avg)), 2)


def calculate_zscore_baseline(
    db: Session,
    player_id: str,
    current_performance_index: Decimal
) -> Optional[Decimal]:
    """
    Calculate z-score of current performance vs player's baseline.

    Args:
        db: Database session
        player_id: Player UUID
        current_performance_index: Current session's performance index

    Returns:
        Z-score or None if insufficient data
    """
    # Get all historical performance indices for this player
    results = db.query(AnalyticsOutputs.performance_index).join(
        SessionModel
    ).filter(
        SessionModel.player_id == player_id
    ).all()

    if not results or len(results) < 3:  # Need at least 3 sessions for meaningful stats
        return None

    indices = [float(r[0]) for r in results]

    try:
        mean = statistics.mean(indices)
        stdev = statistics.stdev(indices)

        if stdev == 0:
            return Decimal("0")

        zscore = (float(current_performance_index) - mean) / stdev
        return round(Decimal(str(zscore)), 3)
    except statistics.StatisticsError:
        return None


def determine_cluster_label(
    pass_accuracy_pct: Optional[Decimal],
    progressive_passes: int,
    successful_dribbles: int,
    interceptions: int,
    sprints_over_25kmh: int,
    distance_km: Decimal,
    tactical_adaptability: Optional[int]
) -> str:
    """
    Determine cluster label based on dominant performance characteristics.

    Returns:
        One of: TECH, TACTIC, PHYSICAL, PSYCH
    """
    scores = {
        "TECH": 0,
        "TACTIC": 0,
        "PHYSICAL": 0,
        "PSYCH": 0
    }

    # Technical indicators
    if pass_accuracy_pct and pass_accuracy_pct > 85:
        scores["TECH"] += 2
    if successful_dribbles > 5:
        scores["TECH"] += 2

    # Tactical indicators
    if progressive_passes > 8:
        scores["TACTIC"] += 2
    if interceptions > 5:
        scores["TACTIC"] += 2

    # Physical indicators
    if sprints_over_25kmh > 15:
        scores["PHYSICAL"] += 2
    if distance_km > Decimal("10"):
        scores["PHYSICAL"] += 2

    # Psychological indicators
    if tactical_adaptability and tactical_adaptability >= 8:
        scores["PSYCH"] += 2

    # Return label with highest score
    return max(scores, key=scores.get)  # type: ignore


def apply_all_calculations(
    db: Session,
    session_id: str,
    player_id: str,
    metrics_physical: MetricsPhysical,
    metrics_technical: MetricsTechnical
) -> dict:
    """
    Apply all calculations for a session and return computed values.

    Args:
        db: Database session
        session_id: Session UUID
        player_id: Player UUID
        metrics_physical: Physical metrics instance
        metrics_technical: Technical metrics instance

    Returns:
        Dictionary with all calculated values
    """
    # Calculate BMI
    bmi = calculate_bmi(metrics_physical.height_cm, metrics_physical.weight_kg)

    # Calculate accuracies
    pass_accuracy = calculate_pass_accuracy(
        metrics_technical.passes_completed,
        metrics_technical.passes_attempted
    )
    shot_accuracy = calculate_shot_accuracy(
        metrics_technical.shots_on_target,
        metrics_technical.shots
    )
    dribble_success = calculate_dribble_success(
        metrics_technical.successful_dribbles,
        metrics_technical.failed_dribbles
    )

    # Get session for coach_rating
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    coach_rating = session.coach_rating if session else None

    # Get tactical metrics for interceptions
    from app.models.models import MetricsTactical, MetricsPsych
    tactical = db.query(MetricsTactical).filter(
        MetricsTactical.session_id == session_id
    ).first()
    psych = db.query(MetricsPsych).filter(
        MetricsPsych.session_id == session_id
    ).first()

    interceptions = tactical.interceptions if tactical else 0
    tactical_adaptability = psych.tactical_adaptability if psych else None

    # Calculate performance index
    performance_index = calculate_performance_index(
        pass_accuracy_pct=pass_accuracy,
        progressive_passes=metrics_technical.progressive_passes,
        interceptions=interceptions,
        successful_dribbles=metrics_technical.successful_dribbles,
        sprints_over_25kmh=metrics_physical.sprints_over_25kmh,
        resting_hr_bpm=metrics_physical.resting_hr_bpm,
        yoyo_level=metrics_physical.yoyo_level,
        distance_km=metrics_physical.distance_km,
        sleep_hours=metrics_physical.sleep_hours,
        coach_rating=coach_rating,
        rpe=metrics_physical.rpe
    )

    # Calculate rolling average (after committing current analytics)
    rolling_avg = calculate_rolling_average(db, player_id, session_id)

    # Calculate z-score
    zscore = calculate_zscore_baseline(db, player_id, performance_index)

    # Determine cluster
    cluster = determine_cluster_label(
        pass_accuracy_pct=pass_accuracy,
        progressive_passes=metrics_technical.progressive_passes,
        successful_dribbles=metrics_technical.successful_dribbles,
        interceptions=interceptions,
        sprints_over_25kmh=metrics_physical.sprints_over_25kmh,
        distance_km=metrics_physical.distance_km,
        tactical_adaptability=tactical_adaptability
    )

    return {
        "bmi": bmi,
        "pass_accuracy_pct": pass_accuracy,
        "shot_accuracy_pct": shot_accuracy,
        "dribble_success_pct": dribble_success,
        "performance_index": performance_index,
        "progress_index_rolling": rolling_avg,
        "zscore_vs_player_baseline": zscore,
        "cluster_label": cluster
    }

"""
ML predictions for player risk and performance insights.
Baseline implementation with mock SHAP explanations.
"""

from datetime import date, datetime, timedelta
from typing import List, Literal, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()


class FeatureContribution(BaseModel):
    """SHAP-style feature contribution."""
    feature_name: str
    value: float
    contribution: float  # Positive means increases risk


class RiskPrediction(BaseModel):
    """Injury risk prediction."""
    player_id: UUID
    prediction_date: date
    risk_score: float  # 0-1
    risk_level: Literal["Low", "Medium", "High", "Very High"]
    top_features: List[FeatureContribution]
    recommendations: List[str]


class PerformanceTrend(BaseModel):
    """Performance trend analysis."""
    player_id: UUID
    metric_key: str
    current_value: float
    trend_7d: float  # % change
    trend_28d: float  # % change
    zscore: float  # Standard deviations from mean
    anomaly: bool  # True if outside 2 std devs


@router.post("/players/{player_id}/predict-risk", response_model=RiskPrediction)
async def predict_injury_risk(
    player_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Predict injury risk for a player based on recent data.

    Uses baseline model with feature engineering from:
    - Training load (sRPE, ACWR)
    - Wellness metrics (sleep, stress, fatigue, DOMS)
    - Match density

    Returns risk score (0-1) and top contributing features (SHAP-like).
    """

    # Get recent data (last 28 days)
    date_from = datetime.now().date() - timedelta(days=28)

    # Calculate ACWR (simplified version)
    acwr_query = text("""
    WITH training_load AS (
        SELECT
            ta.player_id,
            ts.session_date::date AS date,
            COALESCE(ta.rpe_post, 0) * COALESCE(ta.minutes, 0) AS srpe
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        WHERE ta.player_id = :player_id
          AND ts.session_date::date >= :date_from
    ),
    rolling AS (
        SELECT
            AVG(srpe) FILTER (WHERE date >= CURRENT_DATE - 6) AS acute_7d,
            AVG(srpe) FILTER (WHERE date >= CURRENT_DATE - 27) AS chronic_28d
        FROM training_load
    )
    SELECT
        COALESCE(acute_7d, 0) AS acute,
        COALESCE(chronic_28d, 0) AS chronic,
        CASE
            WHEN chronic_28d IS NULL OR chronic_28d = 0 THEN 0
            ELSE acute_7d / chronic_28d
        END AS acwr
    FROM rolling
    """)

    acwr_result = await session.execute(acwr_query, {"player_id": player_id, "date_from": date_from})
    acwr_row = acwr_result.fetchone()

    acute_7d = float(acwr_row[0]) if acwr_row else 0
    chronic_28d = float(acwr_row[1]) if acwr_row else 0
    acwr = float(acwr_row[2]) if acwr_row else 0

    # Get wellness metrics (last 7 days avg)
    wellness_query = text("""
    SELECT
        wm.metric_key,
        AVG(wm.metric_value) AS avg_value,
        STDDEV(wm.metric_value) AS std_value
    FROM wellness_sessions ws
    JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
    WHERE ws.player_id = :player_id
      AND ws.date >= CURRENT_DATE - 6
      AND wm.metric_key IN ('sleep_quality', 'stress', 'fatigue', 'doms')
      AND wm.validity = 'valid'
    GROUP BY wm.metric_key
    """)

    wellness_result = await session.execute(wellness_query, {"player_id": player_id})
    wellness_rows = wellness_result.fetchall()

    wellness_metrics = {row[0]: {"avg": float(row[1]), "std": float(row[2]) if row[2] else 0} for row in wellness_rows}

    # Get match density (matches in last 14 days)
    match_density_query = text("""
    SELECT COUNT(*)::int
    FROM attendances a
    JOIN matches m ON m.id = a.match_id
    WHERE a.player_id = :player_id
      AND m.match_date::date >= CURRENT_DATE - 13
    """)

    match_density_result = await session.execute(match_density_query, {"player_id": player_id})
    match_density = match_density_result.scalar() or 0

    # =========================================================================
    # BASELINE ML MODEL (simplified heuristics)
    # =========================================================================
    # In production, this would load a trained XGBoost model

    risk_score = 0.0
    features = []

    # ACWR risk (optimal 0.8-1.3, higher = risk)
    if acwr > 1.5:
        acwr_risk = min((acwr - 1.5) * 0.3, 0.4)
        risk_score += acwr_risk
        features.append(FeatureContribution(
            feature_name="acwr_7_28",
            value=acwr,
            contribution=acwr_risk
        ))
    elif acwr < 0.5 and acwr > 0:
        acwr_risk = 0.1
        risk_score += acwr_risk
        features.append(FeatureContribution(
            feature_name="acwr_7_28",
            value=acwr,
            contribution=acwr_risk
        ))

    # Sleep quality (low = risk)
    if "sleep_quality" in wellness_metrics:
        sleep_avg = wellness_metrics["sleep_quality"]["avg"]
        if sleep_avg < 6:
            sleep_risk = (6 - sleep_avg) * 0.05
            risk_score += sleep_risk
            features.append(FeatureContribution(
                feature_name="sleep_quality_7d",
                value=sleep_avg,
                contribution=sleep_risk
            ))

    # Stress (high = risk)
    if "stress" in wellness_metrics:
        stress_avg = wellness_metrics["stress"]["avg"]
        if stress_avg > 6:
            stress_risk = (stress_avg - 6) * 0.04
            risk_score += stress_risk
            features.append(FeatureContribution(
                feature_name="stress_7d",
                value=stress_avg,
                contribution=stress_risk
            ))

    # DOMS (high = risk)
    if "doms" in wellness_metrics:
        doms_avg = wellness_metrics["doms"]["avg"]
        if doms_avg > 6:
            doms_risk = (doms_avg - 6) * 0.06
            risk_score += doms_risk
            features.append(FeatureContribution(
                feature_name="doms_7d",
                value=doms_avg,
                contribution=doms_risk
            ))

    # Fatigue (high = risk)
    if "fatigue" in wellness_metrics:
        fatigue_avg = wellness_metrics["fatigue"]["avg"]
        if fatigue_avg > 6:
            fatigue_risk = (fatigue_avg - 6) * 0.05
            risk_score += fatigue_risk
            features.append(FeatureContribution(
                feature_name="fatigue_7d",
                value=fatigue_avg,
                contribution=fatigue_risk
            ))

    # Match density (>3 matches in 14 days = risk)
    if match_density > 3:
        density_risk = (match_density - 3) * 0.08
        risk_score += density_risk
        features.append(FeatureContribution(
            feature_name="match_density_14d",
            value=float(match_density),
            contribution=density_risk
        ))

    # Wellness volatility (high std = risk)
    if "stress" in wellness_metrics and wellness_metrics["stress"]["std"] > 2:
        volatility_risk = 0.08
        risk_score += volatility_risk
        features.append(FeatureContribution(
            feature_name="stress_volatility_7d",
            value=wellness_metrics["stress"]["std"],
            contribution=volatility_risk
        ))

    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)

    # Sort features by contribution (descending)
    features.sort(key=lambda f: f.contribution, reverse=True)

    # Determine risk level
    if risk_score < 0.3:
        risk_level = "Low"
    elif risk_score < 0.5:
        risk_level = "Medium"
    elif risk_score < 0.7:
        risk_level = "High"
    else:
        risk_level = "Very High"

    # Generate recommendations
    recommendations = []
    if acwr > 1.5:
        recommendations.append("⚠️ Reduce training load by 20-30% for 48-72 hours")
        recommendations.append("🔄 Focus on recovery sessions (low intensity)")
    if "sleep_quality" in wellness_metrics and wellness_metrics["sleep_quality"]["avg"] < 6:
        recommendations.append("😴 Improve sleep quality - aim for 8+ hours")
    if "stress" in wellness_metrics and wellness_metrics["stress"]["avg"] > 6:
        recommendations.append("🧘 Stress management - consider yoga/meditation")
    if "doms" in wellness_metrics and wellness_metrics["doms"]["avg"] > 6:
        recommendations.append("💆 Active recovery - massage, stretching, ice bath")
    if match_density > 3:
        recommendations.append("📅 High match density - prioritize rest days")
    if not recommendations:
        recommendations.append("✅ Continue current training regimen")
        recommendations.append("📊 Monitor wellness metrics daily")

    return RiskPrediction(
        player_id=player_id,
        prediction_date=datetime.now().date(),
        risk_score=risk_score,
        risk_level=risk_level,
        top_features=features[:5],  # Top 5 features
        recommendations=recommendations,
    )


@router.get("/players/{player_id}/performance-trends", response_model=List[PerformanceTrend])
async def get_performance_trends(
    player_id: UUID,
    metrics: List[str] = ["sleep_quality", "stress", "fatigue", "doms", "mood"],
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze performance trends for specified metrics.

    Returns trend % (7d and 28d) and z-score for anomaly detection.
    """

    trends = []

    for metric_key in metrics:
        # Get current value (last entry)
        current_query = text("""
        SELECT wm.metric_value
        FROM wellness_sessions ws
        JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE ws.player_id = :player_id
          AND wm.metric_key = :metric_key
          AND wm.validity = 'valid'
        ORDER BY ws.date DESC
        LIMIT 1
        """)

        current_result = await session.execute(current_query, {"player_id": player_id, "metric_key": metric_key})
        current_row = current_result.fetchone()

        if not current_row:
            continue

        current_value = float(current_row[0])

        # Get trends and stats
        trend_query = text("""
        WITH recent_7d AS (
            SELECT AVG(wm.metric_value) AS avg_7d
            FROM wellness_sessions ws
            JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
            WHERE ws.player_id = :player_id
              AND ws.date >= CURRENT_DATE - 6
              AND wm.metric_key = :metric_key
              AND wm.validity = 'valid'
        ),
        recent_28d AS (
            SELECT AVG(wm.metric_value) AS avg_28d, STDDEV(wm.metric_value) AS std_28d
            FROM wellness_sessions ws
            JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
            WHERE ws.player_id = :player_id
              AND ws.date >= CURRENT_DATE - 27
              AND wm.metric_key = :metric_key
              AND wm.validity = 'valid'
        ),
        previous_7d AS (
            SELECT AVG(wm.metric_value) AS avg_prev_7d
            FROM wellness_sessions ws
            JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
            WHERE ws.player_id = :player_id
              AND ws.date BETWEEN CURRENT_DATE - 13 AND CURRENT_DATE - 7
              AND wm.metric_key = :metric_key
              AND wm.validity = 'valid'
        ),
        previous_28d AS (
            SELECT AVG(wm.metric_value) AS avg_prev_28d
            FROM wellness_sessions ws
            JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
            WHERE ws.player_id = :player_id
              AND ws.date BETWEEN CURRENT_DATE - 55 AND CURRENT_DATE - 28
              AND wm.metric_key = :metric_key
              AND wm.validity = 'valid'
        )
        SELECT
            (SELECT avg_7d FROM recent_7d) AS avg_7d,
            (SELECT avg_28d FROM recent_28d) AS avg_28d,
            (SELECT std_28d FROM recent_28d) AS std_28d,
            (SELECT avg_prev_7d FROM previous_7d) AS avg_prev_7d,
            (SELECT avg_prev_28d FROM previous_28d) AS avg_prev_28d
        """)

        trend_result = await session.execute(trend_query, {"player_id": player_id, "metric_key": metric_key})
        trend_row = trend_result.fetchone()

        if not trend_row:
            continue

        avg_7d = float(trend_row[0]) if trend_row[0] else current_value
        avg_28d = float(trend_row[1]) if trend_row[1] else current_value
        std_28d = float(trend_row[2]) if trend_row[2] else 1.0
        avg_prev_7d = float(trend_row[3]) if trend_row[3] else avg_7d
        avg_prev_28d = float(trend_row[4]) if trend_row[4] else avg_28d

        # Calculate trends (% change)
        trend_7d = ((avg_7d - avg_prev_7d) / avg_prev_7d * 100) if avg_prev_7d > 0 else 0
        trend_28d = ((avg_28d - avg_prev_28d) / avg_prev_28d * 100) if avg_prev_28d > 0 else 0

        # Calculate z-score
        zscore = ((current_value - avg_28d) / std_28d) if std_28d > 0 else 0

        # Anomaly detection (>2 std devs)
        anomaly = abs(zscore) > 2

        trends.append(
            PerformanceTrend(
                player_id=player_id,
                metric_key=metric_key,
                current_value=current_value,
                trend_7d=trend_7d,
                trend_28d=trend_28d,
                zscore=zscore,
                anomaly=anomaly,
            )
        )

    return trends

"""Analytics API router - Player statistics and trends."""

from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.player import Player
from app.models.test import PhysicalTest, WellnessData
from app.models.user import User

router = APIRouter()


@router.get("/players/{player_id}/wellness-trends")
async def get_player_wellness_trends(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
):
    """Get wellness trends for a player over time."""
    # Verify player belongs to organization
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Get wellness data
    start_date = date.today() - timedelta(days=days)
    query = (
        select(WellnessData)
        .where(
            WellnessData.player_id == player_id,
            WellnessData.organization_id == current_user.organization_id,
            WellnessData.date >= start_date
        )
        .order_by(WellnessData.date)
    )

    result = await session.execute(query)
    wellness_data = result.scalars().all()

    # Format data for charts
    trends = {
        "dates": [],
        "sleep_hours": [],
        "sleep_quality": [],
        "fatigue": [],
        "stress": [],
        "mood": [],
        "motivation": [],
        "doms": [],
        "training_load": [],
        "resting_hr": [],
    }

    for data in wellness_data:
        trends["dates"].append(data.date.isoformat())
        trends["sleep_hours"].append(data.sleep_hours)
        trends["sleep_quality"].append(data.sleep_quality)
        trends["fatigue"].append(data.fatigue_rating)
        trends["stress"].append(data.stress_rating)
        trends["mood"].append(data.mood_rating)
        trends["motivation"].append(data.motivation_rating)
        trends["doms"].append(data.doms_rating)
        trends["training_load"].append(data.training_load)
        trends["resting_hr"].append(data.resting_hr_bpm)

    return trends


@router.get("/players/{player_id}/training-load")
async def get_player_training_load(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(42, ge=7, le=365, description="Number of days to analyze"),
):
    """Get training load analysis including ACWR (Acute:Chronic Workload Ratio)."""
    # Verify player
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Get wellness data with training load
    start_date = date.today() - timedelta(days=days)
    query = (
        select(WellnessData)
        .where(
            WellnessData.player_id == player_id,
            WellnessData.organization_id == current_user.organization_id,
            WellnessData.date >= start_date,
            WellnessData.training_load.isnot(None)
        )
        .order_by(WellnessData.date)
    )

    result = await session.execute(query)
    wellness_data = result.scalars().all()

    # Calculate ACWR (7-day acute / 28-day chronic)
    daily_loads = []
    acwr_values = []
    cumulative_load = []
    total = 0

    for data in wellness_data:
        load = data.training_load or 0
        daily_loads.append({
            "date": data.date.isoformat(),
            "load": load,
            "srpe": data.srpe,
            "duration": data.session_duration_min
        })
        total += load
        cumulative_load.append(total)

    # Calculate ACWR for each day
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
                "acute_load": acute,
                "chronic_load": chronic
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
        "total_load": total,
        "average_daily_load": round(total / len(daily_loads), 2) if daily_loads else 0
    }


@router.get("/players/{player_id}/physical-evolution")
async def get_player_physical_evolution(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get physical test results evolution over time."""
    # Verify player
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Get physical tests
    query = (
        select(PhysicalTest)
        .where(
            PhysicalTest.player_id == player_id,
            PhysicalTest.organization_id == current_user.organization_id
        )
        .order_by(PhysicalTest.test_date)
    )

    result = await session.execute(query)
    tests = result.scalars().all()

    # Format data
    evolution = {
        "dates": [],
        "weight": [],
        "height": [],
        "bmi": [],
        "body_fat": [],
        "vo2max": [],
        "sprint_20m": [],
        "cmj": [],
        "yoyo_test": [],
    }

    for test in tests:
        evolution["dates"].append(test.test_date.isoformat())
        evolution["weight"].append(test.weight_kg)
        evolution["height"].append(test.height_cm)
        evolution["bmi"].append(test.bmi)
        evolution["body_fat"].append(test.body_fat_pct)
        evolution["vo2max"].append(test.vo2max_ml_kg_min)
        evolution["sprint_20m"].append(test.sprint_20m_s)
        evolution["cmj"].append(test.cmj_cm)
        evolution["yoyo_test"].append(test.yoyo_test_level)

    return evolution


@router.get("/players/{player_id}/summary")
async def get_player_summary(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get comprehensive player summary with latest stats."""
    # Get player
    result = await session.execute(
        select(Player).where(
            Player.id == player_id,
            Player.organization_id == current_user.organization_id
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Get latest wellness data (last 7 days average)
    start_date = date.today() - timedelta(days=7)
    wellness_query = (
        select(
            func.avg(WellnessData.sleep_hours).label("avg_sleep"),
            func.avg(WellnessData.sleep_quality).label("avg_sleep_quality"),
            func.avg(WellnessData.fatigue_rating).label("avg_fatigue"),
            func.avg(WellnessData.stress_rating).label("avg_stress"),
            func.avg(WellnessData.mood_rating).label("avg_mood"),
            func.avg(WellnessData.training_load).label("avg_load"),
            func.sum(WellnessData.training_load).label("total_load"),
        )
        .where(
            WellnessData.player_id == player_id,
            WellnessData.organization_id == current_user.organization_id,
            WellnessData.date >= start_date
        )
    )

    wellness_result = await session.execute(wellness_query)
    wellness_stats = wellness_result.first()

    # Get latest physical test
    latest_test_query = (
        select(PhysicalTest)
        .where(
            PhysicalTest.player_id == player_id,
            PhysicalTest.organization_id == current_user.organization_id
        )
        .order_by(PhysicalTest.test_date.desc())
        .limit(1)
    )

    test_result = await session.execute(latest_test_query)
    latest_test = test_result.scalar_one_or_none()

    # Calculate age
    today = date.today()
    age = (
        today.year - player.date_of_birth.year -
        ((today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day))
    )

    return {
        "player": {
            "id": str(player.id),
            "first_name": player.first_name,
            "last_name": player.last_name,
            "age": age,
            "date_of_birth": player.date_of_birth.isoformat(),
            "role_primary": player.role_primary,
            "role_secondary": player.role_secondary,
            "jersey_number": player.jersey_number,
            "dominant_foot": player.dominant_foot,
            "is_active": player.is_active,
            "is_injured": player.is_injured,
        },
        "wellness_last_7_days": {
            "avg_sleep_hours": round(wellness_stats.avg_sleep, 1) if wellness_stats.avg_sleep else None,
            "avg_sleep_quality": round(wellness_stats.avg_sleep_quality, 1) if wellness_stats.avg_sleep_quality else None,
            "avg_fatigue": round(wellness_stats.avg_fatigue, 1) if wellness_stats.avg_fatigue else None,
            "avg_stress": round(wellness_stats.avg_stress, 1) if wellness_stats.avg_stress else None,
            "avg_mood": round(wellness_stats.avg_mood, 1) if wellness_stats.avg_mood else None,
            "avg_daily_load": round(wellness_stats.avg_load, 1) if wellness_stats.avg_load else None,
            "total_load": round(wellness_stats.total_load, 1) if wellness_stats.total_load else None,
        },
        "latest_physical_test": {
            "date": latest_test.test_date.isoformat() if latest_test else None,
            "weight_kg": latest_test.weight_kg if latest_test else player.weight_kg,
            "height_cm": latest_test.height_cm if latest_test else player.height_cm,
            "bmi": latest_test.bmi if latest_test else player.bmi,
            "body_fat_pct": latest_test.body_fat_pct if latest_test else player.body_fat_pct,
            "vo2max": latest_test.vo2max_ml_kg_min if latest_test else None,
            "sprint_20m_s": latest_test.sprint_20m_s if latest_test else None,
            "cmj_cm": latest_test.cmj_cm if latest_test else None,
        }
    }


@router.get("/players/{player_id}/injury-risk")
async def get_player_injury_risk(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Calculate injury risk (0-1) based on wellness metrics.
    Formula: risk = 0.25·z(HRV↓) + 0.20·z(FC↑) + 0.25·z(Load↑) + 0.15·z(DOMS↑) + 0.15·z(Sleep↓)
    """
    # Get last 7 days wellness
    start_date = date.today() - timedelta(days=7)
    query = (
        select(WellnessData)
        .where(
            WellnessData.player_id == player_id,
            WellnessData.organization_id == current_user.organization_id,
            WellnessData.date >= start_date
        )
        .order_by(WellnessData.date.desc())
    )
    
    result = await session.execute(query)
    recent_wellness = result.scalars().all()
    
    if not recent_wellness:
        return {"injury_risk_0_1": None, "risk_level": "unknown", "factors": {}}
    
    # Calculate averages
    hrv_avg = sum(w.hrv_ms for w in recent_wellness if w.hrv_ms) / max(1, sum(1 for w in recent_wellness if w.hrv_ms))
    hr_avg = sum(w.resting_hr_bpm for w in recent_wellness if w.resting_hr_bpm) / max(1, sum(1 for w in recent_wellness if w.resting_hr_bpm))
    load_avg = sum(w.training_load for w in recent_wellness if w.training_load) / max(1, sum(1 for w in recent_wellness if w.training_load))
    doms_avg = sum(w.doms_rating for w in recent_wellness if w.doms_rating) / max(1, sum(1 for w in recent_wellness if w.doms_rating))
    sleep_avg = sum(w.sleep_hours for w in recent_wellness if w.sleep_hours) / max(1, sum(1 for w in recent_wellness if w.sleep_hours))
    
    # Simple z-score normalization (simplified for demo)
    # In production, use historical player baselines
    hrv_risk = max(0, min(1, 1 - (hrv_avg / 100))) if hrv_avg else 0.5  # Lower HRV = higher risk
    hr_risk = max(0, min(1, (hr_avg - 40) / 60)) if hr_avg else 0.5  # Higher HR = higher risk
    load_risk = max(0, min(1, load_avg / 1000)) if load_avg else 0.5  # Higher load = higher risk
    doms_risk = max(0, min(1, doms_avg / 5)) if doms_avg else 0.5  # Higher DOMS = higher risk
    sleep_risk = max(0, min(1, 1 - (sleep_avg / 10))) if sleep_avg else 0.5  # Less sleep = higher risk
    
    # Weighted sum
    injury_risk = (
        0.25 * hrv_risk +
        0.20 * hr_risk +
        0.25 * load_risk +
        0.15 * doms_risk +
        0.15 * sleep_risk
    )
    
    # Determine risk level
    if injury_risk < 0.33:
        risk_level = "low"
    elif injury_risk < 0.66:
        risk_level = "moderate"
    else:
        risk_level = "high"
    
    return {
        "injury_risk_0_1": round(injury_risk, 3),
        "risk_level": risk_level,
        "factors": {
            "hrv_risk": round(hrv_risk, 2),
            "hr_risk": round(hr_risk, 2),
            "load_risk": round(load_risk, 2),
            "doms_risk": round(doms_risk, 2),
            "sleep_risk": round(sleep_risk, 2),
        },
        "recent_averages": {
            "hrv_ms": round(hrv_avg, 1) if hrv_avg else None,
            "resting_hr_bpm": round(hr_avg, 1) if hr_avg else None,
            "training_load_AU": round(load_avg, 1) if load_avg else None,
            "doms_rating": round(doms_avg, 1) if doms_avg else None,
            "sleep_hours": round(sleep_avg, 1) if sleep_avg else None,
        }
    }


@router.get("/players/{player_id}/evolution-index")
async def get_player_evolution_index(
    player_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Calculate Evolution Index (0-100).
    Weights: Physical 30%, Technical 25%, Tactical 15%, Psychological 15%, Health 15%
    """
    # This is a simplified calculation - in production, compare vs baseline/history
    score_components = {}
    
    # Physical (30%) - from recent wellness + tests
    start_date = date.today() - timedelta(days=30)
    wellness_query = select(WellnessData).where(
        WellnessData.player_id == player_id,
        WellnessData.organization_id == current_user.organization_id,
        WellnessData.date >= start_date
    )
    result = await session.execute(wellness_query)
    wellness_list = result.scalars().all()
    
    if wellness_list:
        avg_hrv = sum(w.hrv_ms for w in wellness_list if w.hrv_ms) / max(1, sum(1 for w in wellness_list if w.hrv_ms)) if any(w.hrv_ms for w in wellness_list) else 50
        physical_score = min(100, (avg_hrv / 100) * 100)  # Simplified
    else:
        physical_score = 50
    
    score_components["physical_score"] = round(physical_score, 1)
    
    # Technical, Tactical, Psychological, Health would be calculated similarly
    # For now, using placeholders
    technical_score = 70  # Placeholder
    tactical_score = 65  # Placeholder
    psychological_score = 75  # Placeholder
    health_score = 80  # Placeholder
    
    score_components["technical_score"] = technical_score
    score_components["tactical_score"] = tactical_score
    score_components["psychological_score"] = psychological_score
    score_components["health_score"] = health_score
    
    # Weighted sum
    evolution_index = (
        0.30 * physical_score +
        0.25 * technical_score +
        0.15 * tactical_score +
        0.15 * psychological_score +
        0.15 * health_score
    )
    
    return {
        "evolution_index_0_100": round(evolution_index, 1),
        "components": score_components,
        "weights": {
            "physical": 0.30,
            "technical": 0.25,
            "tactical": 0.15,
            "psychological": 0.15,
            "health": 0.15
        }
    }

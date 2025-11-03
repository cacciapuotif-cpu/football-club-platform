"""
Quick Input Router - Fast mobile-friendly data entry.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.injury import Injury, InjuryType, InjurySeverity
from app.models.player import Player
from app.models.session import TrainingSession
from app.models.wellness import WellnessData

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# QUICK INPUT SCHEMAS
# ============================================


class QuickWellnessInput(BaseModel):
    """Quick wellness data input for mobile."""

    player_id: UUID
    organization_id: UUID
    date: datetime = Field(default_factory=datetime.utcnow)

    # Quick ratings (1-5 scale)
    fatigue: int = Field(..., ge=1, le=5, description="Fatigue level (1=low, 5=high)")
    mood: int = Field(..., ge=1, le=5, description="Mood (1=poor, 5=excellent)")
    stress: int = Field(..., ge=1, le=5, description="Stress level (1=low, 5=high)")
    sleep_hours: float = Field(..., ge=0, le=12, description="Hours of sleep")

    # Optional quick notes
    notes: Optional[str] = Field(None, max_length=200, description="Quick notes")


class QuickTrainingInput(BaseModel):
    """Quick training session input for mobile."""

    player_id: UUID
    team_id: Optional[UUID] = None
    organization_id: UUID
    date: datetime = Field(default_factory=datetime.utcnow)

    # Quick RPE
    rpe: int = Field(..., ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    duration_min: int = Field(..., ge=5, le=300, description="Duration in minutes")

    # Optional
    session_type: Optional[str] = Field(None, max_length=50, description="Session type")
    notes: Optional[str] = Field(None, max_length=200)


class QuickInjuryReport(BaseModel):
    """Quick injury report for mobile."""

    player_id: UUID
    organization_id: UUID
    injury_date: datetime = Field(default_factory=datetime.utcnow)

    # Quick injury details
    injury_type: str = Field(..., description="Injury type (e.g., MUSCLE, LIGAMENT)")
    body_part: str = Field(..., max_length=100, description="Body part affected")
    severity: str = Field(..., description="Severity (MINOR, MODERATE, SEVERE)")

    # Optional
    description: Optional[str] = Field(None, max_length=300)
    expected_return_days: Optional[int] = Field(None, ge=0, le=365)


class QuickMatchFeedback(BaseModel):
    """Quick match feedback for mobile (simplified)."""

    player_id: UUID
    organization_id: UUID
    match_date: datetime = Field(default_factory=datetime.utcnow)

    # Quick feedback
    minutes_played: int = Field(..., ge=0, le=120)
    self_rating: int = Field(..., ge=1, le=10, description="Self rating (1-10)")

    # Optional performance indicators
    goals: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    notes: Optional[str] = Field(None, max_length=200)


class QuickInputResponse(BaseModel):
    """Generic response for quick input."""

    success: bool
    message: str
    data_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# QUICK INPUT ENDPOINTS
# ============================================


@router.post("/wellness", response_model=QuickInputResponse, status_code=status.HTTP_201_CREATED)
async def quick_wellness_input(
    data: QuickWellnessInput,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick wellness data input - mobile optimized.

    Fast endpoint for players to log daily wellness:
    - Fatigue (1-5)
    - Mood (1-5)
    - Stress (1-5)
    - Sleep hours

    **Mobile usage:**
    - Simple 4-field form
    - Auto-date to today
    - Submit in <30 seconds
    """
    try:
        # Validate player exists
        from sqlalchemy import select

        player_result = await session.execute(select(Player).where(Player.id == data.player_id))
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player {data.player_id} not found",
            )

        # Create wellness record
        wellness = WellnessData(
            player_id=data.player_id,
            organization_id=data.organization_id,
            fatigue=data.fatigue,
            mood=data.mood,
            stress=data.stress,
            sleep_hours=data.sleep_hours,
            notes=data.notes,
            created_at=data.date,
        )

        session.add(wellness)
        await session.commit()
        await session.refresh(wellness)

        logger.info(f"Quick wellness input for player {player.first_name} {player.last_name}")

        return QuickInputResponse(
            success=True,
            message="Wellness data recorded successfully",
            data_id=wellness.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in quick wellness input: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record wellness data: {str(e)}",
        )


@router.post("/training", response_model=QuickInputResponse, status_code=status.HTTP_201_CREATED)
async def quick_training_input(
    data: QuickTrainingInput,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick training session input - mobile optimized.

    Fast endpoint for players to log training:
    - RPE (Rate of Perceived Exertion, 1-10)
    - Duration
    - Optional notes

    **Mobile usage:**
    - 2-field form (RPE + duration)
    - Auto-date to today
    - Submit after training
    """
    try:
        # Validate player exists
        from sqlalchemy import select

        player_result = await session.execute(select(Player).where(Player.id == data.player_id))
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player {data.player_id} not found",
            )

        # Create training session
        training = TrainingSession(
            player_id=data.player_id,
            team_id=data.team_id,
            organization_id=data.organization_id,
            rpe=data.rpe,
            duration_minutes=data.duration_min,
            session_type=data.session_type or "generic",
            notes=data.notes,
            created_at=data.date,
        )

        session.add(training)
        await session.commit()
        await session.refresh(training)

        logger.info(
            f"Quick training input for player {player.first_name} {player.last_name}: RPE={data.rpe}"
        )

        return QuickInputResponse(
            success=True,
            message="Training session recorded successfully",
            data_id=training.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in quick training input: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record training session: {str(e)}",
        )


@router.post("/injury", response_model=QuickInputResponse, status_code=status.HTTP_201_CREATED)
async def quick_injury_report(
    data: QuickInjuryReport,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick injury report - mobile optimized.

    Fast endpoint for reporting injuries:
    - Injury type and body part
    - Severity
    - Expected return time

    **Mobile usage:**
    - 4-field form
    - Immediate reporting
    - Critical for injury tracking
    """
    try:
        # Validate player exists
        from sqlalchemy import select

        player_result = await session.execute(select(Player).where(Player.id == data.player_id))
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player {data.player_id} not found",
            )

        # Parse injury type and severity
        try:
            injury_type_enum = InjuryType[data.injury_type.upper()]
        except KeyError:
            injury_type_enum = InjuryType.OTHER

        try:
            severity_enum = InjurySeverity[data.severity.upper()]
        except KeyError:
            severity_enum = InjurySeverity.MODERATE

        # Calculate expected return date if provided
        expected_return = None
        if data.expected_return_days:
            from datetime import timedelta

            expected_return = data.injury_date.date() + timedelta(days=data.expected_return_days)

        # Create injury record
        injury = Injury(
            player_id=data.player_id,
            organization_id=data.organization_id,
            injury_type=injury_type_enum,
            body_part=data.body_part,
            severity=severity_enum,
            injury_date=data.injury_date,
            description=data.description,
            expected_return_date=expected_return,
        )

        session.add(injury)
        await session.commit()
        await session.refresh(injury)

        logger.warning(
            f"Quick injury report for player {player.first_name} {player.last_name}: {data.body_part} ({data.severity})"
        )

        return QuickInputResponse(
            success=True,
            message="Injury reported successfully",
            data_id=injury.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in quick injury report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report injury: {str(e)}",
        )


@router.post("/match-feedback", response_model=QuickInputResponse, status_code=status.HTTP_201_CREATED)
async def quick_match_feedback(
    data: QuickMatchFeedback,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick match feedback - mobile optimized.

    Fast endpoint for post-match player feedback:
    - Minutes played
    - Self-rating (1-10)
    - Goals/assists
    - Quick notes

    **Mobile usage:**
    - Simple post-match form
    - Player self-assessment
    - Immediate feedback loop
    """
    try:
        # Validate player exists
        from sqlalchemy import select

        player_result = await session.execute(select(Player).where(Player.id == data.player_id))
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player {data.player_id} not found",
            )

        # For quick feedback, we'll store it as a note in wellness data
        # In a full implementation, this would link to actual match attendance

        # Create a wellness record with match feedback
        wellness = WellnessData(
            player_id=data.player_id,
            organization_id=data.organization_id,
            mood=min(5, int(data.self_rating / 2)),  # Convert 1-10 to 1-5
            notes=f"Match feedback: {data.minutes_played}min played, self-rating: {data.self_rating}/10. "
            f"Goals: {data.goals}, Assists: {data.assists}. {data.notes or ''}",
            created_at=data.match_date,
        )

        session.add(wellness)
        await session.commit()
        await session.refresh(wellness)

        logger.info(
            f"Quick match feedback for player {player.first_name} {player.last_name}: {data.self_rating}/10"
        )

        return QuickInputResponse(
            success=True,
            message="Match feedback recorded successfully",
            data_id=wellness.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in quick match feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record match feedback: {str(e)}",
        )


# ============================================
# BULK QUICK INPUT (BONUS)
# ============================================


class BulkQuickInput(BaseModel):
    """Bulk quick input for multiple data types at once."""

    player_id: UUID
    organization_id: UUID
    date: datetime = Field(default_factory=datetime.utcnow)

    # All optional - submit what you have
    wellness: Optional[QuickWellnessInput] = None
    training: Optional[QuickTrainingInput] = None
    injury: Optional[QuickInjuryReport] = None
    match_feedback: Optional[QuickMatchFeedback] = None


@router.post("/bulk", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bulk_quick_input(
    data: BulkQuickInput,
    session: AsyncSession = Depends(get_session),
):
    """
    Bulk quick input - submit multiple data types at once.

    Allows submitting wellness + training + match feedback in one call.

    **Mobile usage:**
    - Single API call for daily check-in
    - Reduce network requests
    - Better UX for daily logging
    """
    results = {"success": True, "submitted": []}

    try:
        # Wellness
        if data.wellness:
            wellness_data = data.wellness
            wellness_data.player_id = data.player_id
            wellness_data.organization_id = data.organization_id
            wellness_data.date = data.date

            result = await quick_wellness_input(wellness_data, session)
            results["submitted"].append({"type": "wellness", "id": str(result.data_id)})

        # Training
        if data.training:
            training_data = data.training
            training_data.player_id = data.player_id
            training_data.organization_id = data.organization_id
            training_data.date = data.date

            result = await quick_training_input(training_data, session)
            results["submitted"].append({"type": "training", "id": str(result.data_id)})

        # Injury
        if data.injury:
            injury_data = data.injury
            injury_data.player_id = data.player_id
            injury_data.organization_id = data.organization_id
            injury_data.injury_date = data.date

            result = await quick_injury_report(injury_data, session)
            results["submitted"].append({"type": "injury", "id": str(result.data_id)})

        # Match feedback
        if data.match_feedback:
            feedback_data = data.match_feedback
            feedback_data.player_id = data.player_id
            feedback_data.organization_id = data.organization_id
            feedback_data.match_date = data.date

            result = await quick_match_feedback(feedback_data, session)
            results["submitted"].append({"type": "match_feedback", "id": str(result.data_id)})

        results["count"] = len(results["submitted"])
        results["message"] = f"Successfully submitted {results['count']} data entries"

        return results

    except Exception as e:
        logger.error(f"Error in bulk quick input: {e}", exc_info=True)
        return {"success": False, "error": str(e), "submitted": results["submitted"]}

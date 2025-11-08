"""
Prescriptions API Router - Training/recovery prescriptions
Team 2 Implementation
"""

from datetime import date, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()


class PrescriptionResponse(BaseModel):
    """Training/recovery prescription."""
    id: str
    player_id: UUID
    created_date: date
    prescription_type: Literal["rest", "load_reduction", "recovery_focus", "maintain"]
    action: str
    intensity_adjustment: str  # e.g., "-20%", "maintain", "+10%"
    duration_days: int
    rationale: str
    confidence: float  # 0-1


@router.get("/{player_id}", response_model=list[PrescriptionResponse])
async def get_player_prescriptions(
    player_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get training/recovery prescriptions for a player.

    **Team 2 Implementation**: Stub endpoint with rule-based prescriptions.
    Team 3 will integrate with actual prescription engine + ML insights.

    **Parameters**:
    - player_id: Player UUID

    **Returns**:
    - List of prescriptions (recent first)
    - Action recommendations
    - Rationale
    """
    # Verify player exists
    from sqlmodel import select
    from app.models.player import Player

    result = await session.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    # Mock prescriptions (Team 2 stub)
    # Team 3 will generate based on actual ML predictions + domain rules
    import hashlib
    player_hash = int(hashlib.md5(str(player_id).encode()).hexdigest(), 16)
    risk_indicator = player_hash % 4  # 0-3

    prescriptions = []

    if risk_indicator == 0:
        # Low risk - maintain
        prescriptions.append(PrescriptionResponse(
            id=f"presc-{player_id}-001",
            player_id=player_id,
            created_date=date.today(),
            prescription_type="maintain",
            action="Continue current training load",
            intensity_adjustment="maintain",
            duration_days=7,
            rationale="Metrics within optimal range. ACWR stable, wellness good.",
            confidence=0.85
        ))
    elif risk_indicator == 1:
        # Medium risk - load reduction
        prescriptions.append(PrescriptionResponse(
            id=f"presc-{player_id}-001",
            player_id=player_id,
            created_date=date.today(),
            prescription_type="load_reduction",
            action="Reduce training volume by 15-20%",
            intensity_adjustment="-20%",
            duration_days=5,
            rationale="Elevated ACWR (>1.3). Slight wellness decline detected.",
            confidence=0.78
        ))
    elif risk_indicator == 2:
        # High risk - recovery focus
        prescriptions.append(PrescriptionResponse(
            id=f"presc-{player_id}-001",
            player_id=player_id,
            created_date=date.today(),
            prescription_type="recovery_focus",
            action="Focus on recovery: active rest, mobility, sleep optimization",
            intensity_adjustment="-40%",
            duration_days=3,
            rationale="High injury risk score (>0.7). Poor sleep quality, elevated fatigue.",
            confidence=0.82
        ))
    else:
        # Very high risk - rest
        prescriptions.append(PrescriptionResponse(
            id=f"presc-{player_id}-001",
            player_id=player_id,
            created_date=date.today(),
            prescription_type="rest",
            action="Complete rest for 48-72h, medical evaluation recommended",
            intensity_adjustment="-100%",
            duration_days=3,
            rationale="Very high injury risk (>0.85). DOMS elevated, match density high.",
            confidence=0.90
        ))

    # Add a second prescription (older)
    prescriptions.append(PrescriptionResponse(
        id=f"presc-{player_id}-002",
        player_id=player_id,
        created_date=date.today() - timedelta(days=7),
        prescription_type="maintain",
        action="Previous: Continue training as planned",
        intensity_adjustment="maintain",
        duration_days=7,
        rationale="Historical prescription from 7 days ago.",
        confidence=0.80
    ))

    return prescriptions

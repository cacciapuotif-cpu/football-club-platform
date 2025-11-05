"""ML Analytics router with UUID support and sync DB."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.db_sync import get_db
from app.models.analytics import PlayerMatchStat, PlayerPrediction
from app.schemas.ml_analytics import PlayerMLSummary
from app.services.ml_analytics_service import train_all, predict_for_player

router = APIRouter(prefix="/analytics", tags=["ML Analytics"])


@router.get("/player/{player_id}/summary", response_model=PlayerMLSummary)
def player_summary(player_id: str, db: Session = Depends(get_db)):
    """Get player ML summary based on recent match stats."""
    stats = (
        db.query(PlayerMatchStat)
        .filter(PlayerMatchStat.player_id == player_id)
        .order_by(PlayerMatchStat.id.desc())
        .limit(10)
        .all()
    )

    if not stats:
        return PlayerMLSummary(
            player_id=player_id,
            last_10_matches=0,
            avg_xg=0.0,
            avg_key_passes=0.0,
            avg_duels_won=0.0,
            trend_form_last_10=0.0,
        )

    avg_xg = sum((s.xg or 0) for s in stats) / len(stats)
    avg_kp = sum((s.key_passes or 0) for s in stats) / len(stats)
    avg_duels = sum((s.duels_won or 0) for s in stats) / len(stats)

    # Trend form
    first5 = stats[5:] if len(stats) > 5 else []
    last5 = stats[:5]
    m1 = (sum((s.xg or 0) for s in first5) / len(first5)) if first5 else 0
    m2 = (sum((s.xg or 0) for s in last5) / len(last5)) if last5 else 0
    trend = m2 - m1

    return PlayerMLSummary(
        player_id=player_id,
        last_10_matches=len(stats),
        avg_xg=avg_xg,
        avg_key_passes=avg_kp,
        avg_duels_won=avg_duels,
        trend_form_last_10=trend,
    )


@router.get("/player/{player_id}/predictions")
def player_predictions(player_id: str, db: Session = Depends(get_db)) -> Dict:
    """Get ML predictions for a player."""
    _ = predict_for_player(player_id)

    preds = (
        db.query(PlayerPrediction)
        .filter(PlayerPrediction.player_id == player_id)
        .order_by(PlayerPrediction.date.desc(), PlayerPrediction.id.desc())
        .limit(10)
        .all()
    )

    return {
        "player_id": player_id,
        "items": [
            dict(
                player_id=str(p.player_id),
                date=p.date,
                target=p.target,
                model_name=p.model_name,
                model_version=p.model_version,
                y_pred=p.y_pred,
                y_proba=p.y_proba,
            )
            for p in preds
        ],
    }


@router.post("/retrain")
def retrain_models():
    """Retrain all ML models."""
    return {"status": "ok", "result": train_all()}


@router.post("/ingest")
def ingest_placeholder():
    """CSV/JSON ingestion placeholder."""
    return {"status": "ok", "message": "CSV/JSON ingestion: todo"}


@router.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@router.get("/players")
def list_players(db: Session = Depends(get_db)):
    """List all players (for frontend)."""
    rows = db.execute(
        "SELECT id, first_name, last_name, role_primary FROM players ORDER BY last_name, first_name"
    ).fetchall()
    return [
        {
            "id": str(r[0]),
            "first_name": r[1] or "",
            "last_name": r[2] or "",
            "name": f"{r[1] or ''} {r[2] or ''}".strip() or str(r[0]),
            "role": r[3] or "UNKNOWN",
        }
        for r in rows
    ]

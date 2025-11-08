"""Seed player sessions step (Team 3) - Auto-link players to their team sessions."""

import random
from decimal import Decimal
from sqlalchemy.orm import Session


def seed(session: Session, data: list[dict]) -> dict:
    """Seed player sessions by auto-linking all players to their team's training sessions.

    This step doesn't use YAML data - it auto-generates based on existing players and sessions.

    Returns dict with created/updated/skipped counts.
    """
    from app.models.player import Player
    from app.models.session import TrainingSession
    from app.models.player_session import PlayerSession

    created = 0
    skipped = 0

    # Get all players
    all_players = session.query(Player).all()

    for player in all_players:
        # Get all training sessions for this player's team
        team_sessions = session.query(TrainingSession).filter(
            TrainingSession.team_id == player.team_id
        ).all()

        for training_session in team_sessions:
            # Check if player_session already exists
            existing = session.query(PlayerSession).filter(
                PlayerSession.player_id == player.id,
                PlayerSession.session_id == training_session.id
            ).first()

            if existing:
                skipped += 1
                continue

            # Generate realistic RPE based on session intensity
            intensity_rpe_map = {
                "low": (1, 3),
                "moderate": (4, 6),
                "high": (7, 8),
                "very_high": (9, 10),
            }

            intensity = training_session.intensity or "moderate"
            rpe_range = intensity_rpe_map.get(intensity.lower(), (5, 7))
            rpe = Decimal(random.randint(rpe_range[0], rpe_range[1]))

            # Calculate session_load = rpe × duration_min
            session_load = rpe * Decimal(training_session.duration_min or 90)

            # Create player_session
            player_session = PlayerSession(
                player_id=player.id,
                session_id=training_session.id,
                rpe=rpe,
                session_load=session_load
            )

            session.add(player_session)
            created += 1

    session.commit()

    return {"created": created, "updated": 0, "skipped": skipped}

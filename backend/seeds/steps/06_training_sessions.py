"""Seed training sessions step (Team 3)."""

from sqlalchemy.orm import Session

from seeds.utils import upsert


def seed(session: Session, data: list[dict]) -> dict:
    """Seed training sessions.

    Returns dict with created/updated/skipped counts.
    """
    from datetime import datetime
    from app.models.session import TrainingSession, SessionType
    from app.models.organization import Organization
    from app.models.team import Team

    created = 0
    updated = 0
    skipped = 0

    for item in data:
        # Get organization
        org = session.query(Organization).filter(
            Organization.slug == item["organization_slug"]
        ).first()

        if not org:
            print(f"⚠️  Organization {item['organization_slug']} not found, skipping session")
            skipped += 1
            continue

        # Get team
        team = session.query(Team).filter(
            Team.organization_id == org.id,
            Team.name == item["team_name"]
        ).first()

        if not team:
            print(f"⚠️  Team {item['team_name']} not found, skipping session")
            skipped += 1
            continue

        # Parse session_type
        session_type_str = item.get("session_type", "training").upper()
        try:
            session_type = SessionType[session_type_str]
        except KeyError:
            session_type = SessionType.TRAINING

        # Map intensity to SessionIntensity enum
        from app.models.session import SessionIntensity
        intensity_str = item.get("intensity", "medium")
        intensity_map = {
            "low": SessionIntensity.LOW,
            "moderate": SessionIntensity.MEDIUM,
            "medium": SessionIntensity.MEDIUM,
            "high": SessionIntensity.HIGH,
            "very_high": SessionIntensity.HIGH,  # Map to HIGH since VERY_HIGH doesn't exist
        }
        intensity = intensity_map.get(intensity_str.lower(), SessionIntensity.MEDIUM)

        # Parse session date
        session_date = datetime.strptime(item["session_date"], "%Y-%m-%d").date()

        # Check if session already exists (by org, team, date)
        existing = session.query(TrainingSession).filter(
            TrainingSession.organization_id == org.id,
            TrainingSession.team_id == team.id,
            TrainingSession.session_date == session_date
        ).first()

        if existing:
            skipped += 1
            continue

        # Create new session
        new_session = TrainingSession(
            organization_id=org.id,
            team_id=team.id,
            session_date=session_date,
            session_type=session_type,
            duration_min=item.get("duration_min", 90),
            intensity=intensity,
            focus_area=item.get("focus_area"),
            focus=item.get("focus", item.get("session_name")),  # Use session_name as focus if present
            description=item.get("description"),
            coach_notes=item.get("notes"),
        )

        session.add(new_session)
        created += 1

    session.commit()

    return {"created": created, "updated": updated, "skipped": skipped}

"""
Step 05: Players (Robust Idempotent Version)
Dependencies: Organization (FK: organization_id), Team (FK: team_id, nullable)

Strategia chiave naturale (idempotenza robusta):

1) Se presente, usiamo external_id come chiave naturale (glob per dataset).
2) In assenza di external_id, usiamo COMPOSITE KEY:
   (organization_id, team_id, jersey_number) — sufficiente in ambito giovanili/1ª squadra.
   Se jersey_number manca, ripieghiamo su (organization_id, team_id, last_name, first_name, date_of_birth).

Prerequisiti:
- Steps 01_organizations, 03_teams eseguiti con slug/codes coerenti.
- Dataset YAML deve valorizzare almeno: organization_slug, team_name (or team_code),
  first_name, last_name, jersey_number (consigliata), optional: external_id.

Logging:
- Alla fine stampa: inserted / updated / skipped.
"""

from datetime import date
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerRole, DominantFoot, DominantArm
from app.models.organization import Organization
from app.models.team import Team
from seeds.utils import (
    tx,
    fetch_one,
    upsert_advanced,
    log_info,
    log_warn,
    log_error,
)


def _resolve_org(session: Session, org_slug: str) -> Dict[str, Any] | None:
    """Resolve organization by slug."""
    return fetch_one(
        session,
        "SELECT id, slug, name FROM organizations WHERE slug = :slug",
        {"slug": org_slug}
    )


def _resolve_team(
    session: Session,
    org_id: str,
    team_name: str | None,
    team_code: str | None
) -> Dict[str, Any] | None:
    """Resolve team by name or code within organization."""
    if team_name:
        return fetch_one(
            session,
            """
            SELECT id, name, category
            FROM teams
            WHERE organization_id = :org_id AND name = :name
            """,
            {"org_id": org_id, "name": team_name}
        )
    if team_code:
        return fetch_one(
            session,
            """
            SELECT id, name, category
            FROM teams
            WHERE organization_id = :org_id AND category = :code
            """,
            {"org_id": org_id, "code": team_code}
        )
    return None


def seed(session: Session, data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Seed players with robust idempotent strategy.

    Natural key strategies (in order):
    1. external_id (if present)
    2. (organization_id, team_id, jersey_number) if jersey_number present
    3. (organization_id, team_id, last_name, first_name, date_of_birth) fallback

    Returns:
        Statistics dict: {"Players": {"inserted": X, "updated": Y, "skipped": Z}}
    """
    items = data if isinstance(data, list) else []

    if not items:
        log_warn("05_players: nessun player nel dataset (lista vuota). Skipping.")
        return {"Players": {"inserted": 0, "updated": 0, "skipped": 0}}

    inserted = 0
    updated = 0
    skipped = 0
    errors = 0

    for i, raw in enumerate(items, start=1):
        try:
            # Parse input
            first_name = raw.get("first_name", "").strip()
            last_name = raw.get("last_name", "").strip()
            org_slug = raw.get("organization_slug", "").strip()
            team_name = raw.get("team_name")
            team_code = raw.get("team_code")
            external_id = raw.get("external_id")
            jersey_number = raw.get("jersey_number")
            dob_raw = raw.get("date_of_birth")

            # Validation
            if not first_name or not last_name or not org_slug:
                log_warn(
                    f"05_players riga {i}: campi minimi mancanti "
                    f"(first_name/last_name/organization_slug) → skipped"
                )
                skipped += 1
                continue

            # Resolve organization
            org = _resolve_org(session, org_slug)
            if not org:
                log_warn(
                    f"05_players riga {i}: organization_slug '{org_slug}' "
                    f"non trovato → skipped"
                )
                skipped += 1
                continue

            # Resolve team
            team = _resolve_team(session, org["id"], team_name, team_code)
            if not team:
                log_warn(
                    f"05_players riga {i}: team non trovato "
                    f"(org='{org_slug}', name='{team_name}', code='{team_code}') → skipped"
                )
                skipped += 1
                continue

            # Parse date
            if isinstance(dob_raw, str):
                date_of_birth = date.fromisoformat(dob_raw)
            else:
                date_of_birth = dob_raw

            # Parse enums
            role_primary = raw.get("role_primary")
            if role_primary and isinstance(role_primary, str):
                role_primary = PlayerRole(role_primary)

            role_secondary = raw.get("role_secondary")
            if role_secondary and isinstance(role_secondary, str):
                role_secondary = PlayerRole(role_secondary)

            dominant_foot = raw.get("dominant_foot", "RIGHT")
            if isinstance(dominant_foot, str):
                dominant_foot = DominantFoot(dominant_foot)

            dominant_arm = raw.get("dominant_arm", "RIGHT")
            if isinstance(dominant_arm, str):
                dominant_arm = DominantArm(dominant_arm)

            # Build payload
            payload = {
                "organization_id": str(org["id"]),
                "team_id": str(team["id"]) if team else None,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth,
                "nationality": raw.get("nationality", "IT"),
                "role_primary": role_primary,
                "role_secondary": role_secondary,
                "dominant_foot": dominant_foot,
                "dominant_arm": dominant_arm,
                "jersey_number": jersey_number,
                "height_cm": raw.get("height_cm"),
                "weight_kg": raw.get("weight_kg"),
                "is_minor": raw.get("is_minor", False),
                "is_active": raw.get("is_active", True),
                "injury_prone": raw.get("injury_prone", False),
                "consent_given": raw.get("consent_given", True),
                "medical_clearance": raw.get("medical_clearance", True),
                # Tactical/mental attributes
                "tactical_awareness": raw.get("tactical_awareness", 50),
                "positioning": raw.get("positioning", 50),
                "decision_making": raw.get("decision_making", 50),
                "work_rate": raw.get("work_rate", 50),
                "mental_strength": raw.get("mental_strength", 50),
                "leadership": raw.get("leadership", 50),
                "concentration": raw.get("concentration", 50),
                "adaptability": raw.get("adaptability", 50),
            }

            # Add external_id if present
            if external_id:
                payload["external_id"] = external_id

            # Guardian info for minors
            if raw.get("guardian_name"):
                payload["guardian_name"] = raw["guardian_name"]
            if raw.get("guardian_email"):
                payload["guardian_email"] = raw["guardian_email"]
            if raw.get("guardian_phone"):
                payload["guardian_phone"] = raw["guardian_phone"]

            # Define unique key strategies (in order of priority)
            unique_keys = []
            if external_id:
                unique_keys.append(("external_id",))
            if jersey_number:
                unique_keys.append(("organization_id", "team_id", "jersey_number"))
            # Fallback: composite identity
            unique_keys.append(("organization_id", "team_id", "last_name", "first_name", "date_of_birth"))

            # Upsert with advanced strategy
            result = upsert_advanced(
                session=session,
                table="players",
                values=payload,
                unique_keys=unique_keys
            )

            if result == "inserted":
                inserted += 1
                log_info(
                    f"05_players: inserted → {first_name} {last_name} "
                    f"(team={team.get('name')}, jersey={jersey_number or 'N/A'})"
                )
            elif result == "updated":
                updated += 1
                log_info(
                    f"05_players: updated → {first_name} {last_name} "
                    f"(team={team.get('name')}, jersey={jersey_number or 'N/A'})"
                )
            else:  # skipped
                skipped += 1

        except Exception as e:
            errors += 1
            log_error(f"05_players: errore su riga {i}: {e}")
            # Continue with next player (non-strict mode)
            continue

    # Final stats
    log_info(
        f"05_players: Players inserted={inserted}, updated={updated}, "
        f"skipped={skipped}, errors={errors}"
    )

    return {
        "Players": {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
        }
    }

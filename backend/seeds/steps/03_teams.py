"""
Step 03: Teams
Dependencies: Organization (FK: organization_id), Season (FK: season_id, nullable)
"""

from typing import Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.team import Team, Season
from app.models.organization import Organization
from seeds.utils import upsert, get_or_fail


def seed(session: Session, data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Seed teams.

    Natural key: (organization_id, name, season_id)
    References:
        - organization_slug -> Organization
        - season_name -> Season (optional)
    """
    items = data if isinstance(data, list) else []

    if not items:
        return {}

    stats = {"create": 0, "update": 0, "skip": 0}

    for item in items:
        # Resolve organization FK
        org_slug = item.pop("organization_slug")
        org = get_or_fail(session, Organization, slug=org_slug)

        # Resolve season FK (optional)
        season_id = None
        if "season_name" in item:
            season_name = item.pop("season_name")
            season_stmt = select(Season).where(
                Season.organization_id == org.id,
                Season.name == season_name
            )
            season = session.execute(season_stmt).scalar_one_or_none()
            if season:
                season_id = season.id
            else:
                raise ValueError(
                    f"Season '{season_name}' not found for organization '{org_slug}'"
                )

        # Upsert
        keys = {
            "organization_id": org.id,
            "name": item["name"],
        }
        defaults = {k: v for k, v in item.items() if k != "name"}
        if season_id:
            defaults["season_id"] = season_id

        _, op = upsert(session, Team, keys=keys, defaults=defaults)
        stats[op] += 1

    return {"Teams": stats}

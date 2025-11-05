"""
Step 02: Seasons
Dependencies: Organization (FK: organization_id)
"""

from datetime import date
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.team import Season
from app.models.organization import Organization
from seeds.utils import upsert, get_or_fail, print_stats, validate_unique_keys


def seed(session: Session, data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Seed seasons.

    Natural key: (organization_id, name)
    References: organization_slug -> Organization
    """
    items = data if isinstance(data, list) else []

    if not items:
        return {}

    stats = {"create": 0, "update": 0, "skip": 0}

    for item in items:
        # Resolve organization FK
        org_slug = item.pop("organization_slug")
        org = get_or_fail(session, Organization, slug=org_slug)

        # Parse dates
        if isinstance(item.get("start_date"), str):
            item["start_date"] = date.fromisoformat(item["start_date"])
        if isinstance(item.get("end_date"), str):
            item["end_date"] = date.fromisoformat(item["end_date"])

        # Upsert
        keys = {"organization_id": org.id, "name": item["name"]}
        defaults = {k: v for k, v in item.items() if k != "name"}

        _, op = upsert(session, Season, keys=keys, defaults=defaults)
        stats[op] += 1

    return {"Seasons": stats}

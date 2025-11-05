"""
Step 01: Organizations (Root entity)
No dependencies - can be seeded first.
"""

from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.organization import Organization
from seeds.utils import bulk_upsert, validate_unique_keys


def seed(session: Session, data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Seed organizations.

    Natural key: slug
    """
    items = data if isinstance(data, list) else []

    if not items:
        return {}

    # Validate unique slugs
    validate_unique_keys(items, key_fields=["slug"], entity="Organization")

    # Bulk upsert
    stats = bulk_upsert(
        session,
        Organization,
        items=items,
        key_fields=["slug"]
    )

    return {"Organizations": stats}

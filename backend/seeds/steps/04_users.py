"""
Step 04: Users
Dependencies: Organization (FK: organization_id)
"""

from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from seeds.utils import upsert, get_or_fail


def seed(session: Session, data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Seed users.

    Natural key: email
    References: organization_slug -> Organization

    Note: Passwords are hashed before storage.
    """
    items = data if isinstance(data, list) else []

    if not items:
        return {}

    stats = {"create": 0, "update": 0, "skip": 0}

    # Import password hashing utility
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except ImportError:
        # Fallback if passlib not installed
        import hashlib
        class FallbackContext:
            @staticmethod
            def hash(password: str) -> str:
                return hashlib.sha256(password.encode()).hexdigest()
        pwd_context = FallbackContext()

    for item in items:
        # Resolve organization FK
        org_slug = item.pop("organization_slug")
        org = get_or_fail(session, Organization, slug=org_slug)

        # Hash password
        plain_password = item.pop("password", None)
        hashed_password = pwd_context.hash(plain_password) if plain_password else None

        # Upsert
        keys = {"email": item["email"]}
        defaults = {k: v for k, v in item.items() if k != "email"}
        defaults["organization_id"] = org.id
        if hashed_password:
            defaults["hashed_password"] = hashed_password

        _, op = upsert(session, User, keys=keys, defaults=defaults)
        stats[op] += 1

    return {"Users": stats}

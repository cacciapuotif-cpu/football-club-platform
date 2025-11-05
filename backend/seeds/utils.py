"""
Seed Utilities - Transaction Management & Idempotent Upsert
Provides safe, idempotent database operations for seeding.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, TypeVar
from uuid import UUID
import sys

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)
SeedOp = Literal["create", "update", "skip", "inserted", "updated", "skipped"]

# ============================================================================
# TRANSACTION CONTEXT MANAGER
# ============================================================================

@contextmanager
def tx(session: Session):
    """
    Transaction context manager with automatic commit/rollback.

    Usage:
        with tx(session):
            # ... database operations
            # commits on success, rolls back on exception
    """
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


# ============================================================================
# IDEMPOTENT UPSERT
# ============================================================================

def upsert(
    session: Session,
    model: Type[T],
    keys: Dict[str, Any],
    defaults: Dict[str, Any]
) -> Tuple[T, SeedOp]:
    """
    Idempotent upsert: creates if missing, updates if changed, skips if identical.

    Args:
        session: SQLAlchemy session
        model: SQLModel class (e.g., Organization, Player)
        keys: Natural key fields for lookup (e.g., {"slug": "demo-fc"})
        defaults: Additional fields to set/update

    Returns:
        (instance, operation) where operation is "create", "update", or "skip"

    Example:
        org, op = upsert(
            session,
            Organization,
            keys={"slug": "demo-fc"},
            defaults={"name": "Demo FC", "country": "IT"}
        )
        # op will be "create" (new), "update" (changed), or "skip" (identical)
    """
    # Try to find existing instance by natural keys
    stmt = select(model).filter_by(**keys)
    inst = session.execute(stmt).scalar_one_or_none()

    if inst:
        # Instance exists - check if update needed
        changed = False
        for key, value in defaults.items():
            current = getattr(inst, key, None)

            # Handle UUID comparison
            if isinstance(current, UUID) and isinstance(value, str):
                value = UUID(value)

            if current != value:
                setattr(inst, key, value)
                changed = True

        if changed:
            session.flush()
            return inst, "update"
        else:
            return inst, "skip"

    # Instance does not exist - create new
    inst = model(**{**keys, **defaults})
    session.add(inst)

    try:
        session.flush()
        return inst, "create"
    except IntegrityError:
        # Race condition: another process created it
        session.rollback()
        inst = session.execute(stmt).scalar_one()

        # Apply defaults to existing instance
        for key, value in defaults.items():
            setattr(inst, key, value)

        session.flush()
        return inst, "update"


# ============================================================================
# BULK UPSERT
# ============================================================================

def bulk_upsert(
    session: Session,
    model: Type[T],
    items: list[Dict[str, Any]],
    key_fields: list[str]
) -> Dict[SeedOp, int]:
    """
    Bulk upsert multiple items efficiently.

    Args:
        session: SQLAlchemy session
        model: SQLModel class
        items: List of dicts with data
        key_fields: List of field names to use as natural keys

    Returns:
        Statistics dict: {"create": 5, "update": 2, "skip": 3}

    Example:
        stats = bulk_upsert(
            session,
            Player,
            [
                {"first_name": "Marco", "last_name": "Rossi", ...},
                {"first_name": "Luca", "last_name": "Bianchi", ...},
            ],
            key_fields=["first_name", "last_name"]
        )
    """
    stats: Dict[SeedOp, int] = {"create": 0, "update": 0, "skip": 0}

    for item in items:
        keys = {k: v for k, v in item.items() if k in key_fields}
        defaults = {k: v for k, v in item.items() if k not in key_fields}

        _, op = upsert(session, model, keys, defaults)
        stats[op] += 1

    return stats


# ============================================================================
# HELPERS
# ============================================================================

def get_by_natural_key(
    session: Session,
    model: Type[T],
    **filters
) -> T | None:
    """
    Retrieve an instance by natural key.

    Example:
        org = get_by_natural_key(session, Organization, slug="demo-fc")
    """
    stmt = select(model).filter_by(**filters)
    return session.execute(stmt).scalar_one_or_none()


def get_or_fail(
    session: Session,
    model: Type[T],
    **filters
) -> T:
    """
    Retrieve an instance or raise if not found.

    Example:
        org = get_or_fail(session, Organization, slug="demo-fc")
    """
    inst = get_by_natural_key(session, model, **filters)
    if inst is None:
        raise ValueError(
            f"{model.__name__} not found with filters: {filters}"
        )
    return inst


def print_stats(stats: Dict[SeedOp, int], entity: str):
    """
    Pretty-print seed statistics.

    Example:
        print_stats({"create": 5, "update": 2, "skip": 3}, "Players")
        # Output: ✅ Players: 5 created, 2 updated, 3 skipped
    """
    total = sum(stats.values())
    print(
        f"✅ {entity}: "
        f"{stats['create']} created, "
        f"{stats['update']} updated, "
        f"{stats['skip']} skipped "
        f"(total: {total})"
    )


# ============================================================================
# VALIDATION
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required: list[str], entity: str):
    """
    Validate that all required fields are present and non-None.

    Raises:
        ValueError if any required field is missing
    """
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        raise ValueError(
            f"{entity}: Missing required fields: {', '.join(missing)}"
        )


def validate_unique_keys(
    items: list[Dict[str, Any]],
    key_fields: list[str],
    entity: str
):
    """
    Validate that natural keys are unique within the dataset.

    Raises:
        ValueError if duplicate keys found
    """
    seen_keys = set()
    for item in items:
        key_tuple = tuple(item.get(k) for k in key_fields)
        if key_tuple in seen_keys:
            raise ValueError(
                f"{entity}: Duplicate key found: {dict(zip(key_fields, key_tuple))}"
            )
        seen_keys.add(key_tuple)


# ============================================================================
# LOGGING HELPERS
# ============================================================================

def log_info(message: str):
    """Log info message."""
    print(f"ℹ️  {message}", file=sys.stdout)


def log_warn(message: str):
    """Log warning message."""
    print(f"⚠️  {message}", file=sys.stderr)


def log_error(message: str):
    """Log error message."""
    print(f"❌ {message}", file=sys.stderr)


# ============================================================================
# DATABASE QUERY HELPERS
# ============================================================================

def fetch_one(session: Session, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Execute SQL query and fetch one result as dict.

    Args:
        session: SQLAlchemy session
        query: SQL query string
        params: Query parameters

    Returns:
        Dict with column names as keys, or None if no result
    """
    result = session.execute(text(query), params or {})
    row = result.fetchone()
    if row is None:
        return None
    return dict(row._mapping)


def fetch_all(session: Session, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute SQL query and fetch all results as list of dicts.

    Args:
        session: SQLAlchemy session
        query: SQL query string
        params: Query parameters

    Returns:
        List of dicts with column names as keys
    """
    result = session.execute(text(query), params or {})
    return [dict(row._mapping) for row in result.fetchall()]


# ============================================================================
# ADVANCED UPSERT (with unique_keys support)
# ============================================================================

def upsert_advanced(
    session: Session,
    table: str,
    values: Dict[str, Any],
    key: Optional[Dict[str, Any]] = None,
    unique_keys: Optional[List[Tuple[str, ...]]] = None
) -> SeedOp:
    """
    Advanced upsert with support for multiple unique key strategies.

    Args:
        session: SQLAlchemy session
        table: Table name
        values: Data to insert/update
        key: Primary key dict for direct UPDATE (e.g., {"id": 123})
        unique_keys: List of unique key tuples to try in order
                     e.g., [("external_id",), ("org_id", "team_id", "jersey")]

    Returns:
        "inserted" | "updated" | "skipped"

    Strategy:
    1. If key provided: UPDATE directly if exists, INSERT if not
    2. If unique_keys provided: Try each unique key set to find existing record
    3. Compare values, UPDATE if changed, skip if identical
    """
    # Case 1: Direct update by primary key
    if key:
        # Build WHERE clause
        where_parts = [f"{k} = :{k}" for k in key.keys()]
        where_clause = " AND ".join(where_parts)

        # Check if exists
        check_query = f"SELECT * FROM {table} WHERE {where_clause}"
        existing = fetch_one(session, check_query, key)

        if existing:
            # Check if update needed
            changed = False
            for k, v in values.items():
                if existing.get(k) != v:
                    changed = True
                    break

            if not changed:
                return "skipped"

            # Build UPDATE
            set_parts = [f"{k} = :{k}" for k in values.keys()]
            set_clause = ", ".join(set_parts)
            update_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            params = {**values, **key}
            session.execute(text(update_query), params)
            return "updated"
        else:
            # INSERT (key not found)
            cols = ", ".join(values.keys())
            vals = ", ".join(f":{k}" for k in values.keys())
            insert_query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
            session.execute(text(insert_query), values)
            return "inserted"

    # Case 2: Try unique keys to find existing record
    if unique_keys:
        for uk_tuple in unique_keys:
            # Build WHERE for this unique key
            uk_values = {k: values.get(k) for k in uk_tuple if k in values}

            # Skip if any key is None
            if any(v is None for v in uk_values.values()):
                continue

            where_parts = [f"{k} = :{k}" for k in uk_values.keys()]
            where_clause = " AND ".join(where_parts)

            check_query = f"SELECT * FROM {table} WHERE {where_clause}"
            existing = fetch_one(session, check_query, uk_values)

            if existing:
                # Found by this unique key - check if update needed
                changed = False
                for k, v in values.items():
                    if existing.get(k) != v:
                        changed = True
                        break

                if not changed:
                    return "skipped"

                # UPDATE
                set_parts = [f"{k} = :{k}" for k in values.keys()]
                set_clause = ", ".join(set_parts)
                update_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

                params = {**values, **uk_values}
                session.execute(text(update_query), params)
                return "updated"

    # Case 3: No existing record found - INSERT
    cols = ", ".join(values.keys())
    vals = ", ".join(f":{k}" for k in values.keys())
    insert_query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"

    try:
        session.execute(text(insert_query), values)
        return "inserted"
    except IntegrityError:
        # Race condition or constraint violation
        session.rollback()
        return "skipped"

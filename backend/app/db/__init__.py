"""
Database utilities and RLS policies for Football Club Platform.
"""

from pathlib import Path

# Path to RLS policies SQL file
RLS_POLICIES_SQL = Path(__file__).parent / "rls_policies.sql"


def get_rls_policies_sql() -> str:
    """
    Load and return RLS policies SQL content.

    Returns:
        str: SQL content for RLS policies
    """
    with open(RLS_POLICIES_SQL, "r") as f:
        return f.read()


__all__ = ["get_rls_policies_sql", "RLS_POLICIES_SQL"]

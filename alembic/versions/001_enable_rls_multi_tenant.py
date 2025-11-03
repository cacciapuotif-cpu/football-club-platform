"""Enable RLS for multi-tenant isolation

Revision ID: 001_enable_rls
Revises:
Create Date: 2025-01-17

This migration enables Row Level Security (RLS) on all tenant-scoped tables.
Uses organization_id as tenant_id for strict data isolation.
"""

from alembic import op


# revision identifiers
revision = '001_enable_rls'
down_revision = None
branch_labels = None
depends_on = None


# Tables that require RLS (have organization_id)
TENANT_TABLES = [
    'users',
    'players',
    'teams',
    'training_sessions',
    'wellness_data',
    'performance_metrics',
    'videos',
    'video_analyses',
    'reports',
    'injuries',
    'training_plans',
    'matches',
    'match_events',
    'sensor_data',
    'ml_predictions',
    'ml_model_metrics',
    'benchmark_data',
    'audit_logs',
    'advanced_tracking_metrics',
]


def upgrade() -> None:
    """Enable RLS policies on all tenant tables."""

    # Enable RLS on each table
    for table in TENANT_TABLES:
        op.execute(f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
        """)

        # Create policy: users can only see their tenant's data
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (organization_id = current_setting('app.tenant_id', true)::uuid);
        """)

        # Policy for INSERT
        op.execute(f"""
            CREATE POLICY tenant_isolation_insert ON {table}
            FOR INSERT
            WITH CHECK (organization_id = current_setting('app.tenant_id', true)::uuid);
        """)

        # Policy for UPDATE
        op.execute(f"""
            CREATE POLICY tenant_isolation_update ON {table}
            FOR UPDATE
            USING (organization_id = current_setting('app.tenant_id', true)::uuid);
        """)

        # Policy for DELETE
        op.execute(f"""
            CREATE POLICY tenant_isolation_delete ON {table}
            FOR DELETE
            USING (organization_id = current_setting('app.tenant_id', true)::uuid);
        """)

    print(f"✅ RLS enabled on {len(TENANT_TABLES)} tables")


def downgrade() -> None:
    """Disable RLS policies."""

    for table in TENANT_TABLES:
        # Drop policies
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_delete ON {table};")

        # Disable RLS
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    print(f"✅ RLS disabled on {len(TENANT_TABLES)} tables")

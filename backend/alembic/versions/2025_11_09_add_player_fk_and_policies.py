"""add player link to athletes and wellness policies table

Revision ID: 2025_11_09_add_player_fk_and_policies
Revises: 2025_11_08_init_sessions_wellness
Create Date: 2025-11-09 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2025_11_09_add_player_fk_and_policies"
down_revision: str | None = "2025_11_08_init_sessions_wellness"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add player_id column to athletes
    op.add_column(
        "athletes",
        sa.Column("player_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_athletes_player_id_players",
        "athletes",
        "players",
        ["player_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint("uix_athletes_player", "athletes", ["tenant_id", "player_id"])

    # Create wellness_policies table
    op.create_table(
        "wellness_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thresholds", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cooldown_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("min_data_completeness", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index("ix_wellness_policies_tenant_id", "wellness_policies", ["tenant_id"])
    op.create_foreign_key(
        "fk_wellness_policies_tenant",
        "wellness_policies",
        "organizations",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Enable RLS for new table
    op.execute("ALTER TABLE wellness_policies ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY wellness_policies_tenant_isolation
        ON wellness_policies
        USING (tenant_id = current_setting('app.tenant_id')::uuid);
        """
    )


def downgrade() -> None:
    # Drop wellness policies table and policy
    op.execute("DROP POLICY IF EXISTS wellness_policies_tenant_isolation ON wellness_policies;")
    op.drop_constraint("fk_wellness_policies_tenant", "wellness_policies", type_="foreignkey")
    op.drop_index("ix_wellness_policies_tenant_id", table_name="wellness_policies")
    op.drop_table("wellness_policies")

    # Drop player_id column and constraints from athletes
    op.drop_constraint("uix_athletes_player", "athletes", type_="unique")
    op.drop_constraint("fk_athletes_player_id_players", "athletes", type_="foreignkey")
    op.drop_column("athletes", "player_id")


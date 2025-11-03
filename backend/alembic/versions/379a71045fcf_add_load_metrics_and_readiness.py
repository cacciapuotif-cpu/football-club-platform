"""add_load_metrics_and_readiness

Revision ID: 379a71045fcf
Revises: df22d5bc8656
Create Date: 2025-10-28 13:17:50.681604

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '379a71045fcf'
down_revision = 'df22d5bc8656'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add player_metrics_daily table for ACWR, Monotony, Strain, and Readiness tracking."""

    # Create player_metrics_daily table
    op.create_table(
        'player_metrics_daily',
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('acwr', sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column('monotony', sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column('strain', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('readiness', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('player_id', 'date')
    )

    # Create index for efficient queries
    op.create_index(
        'idx_metrics_player_date',
        'player_metrics_daily',
        ['player_id', sa.text('date DESC')],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove player_metrics_daily table."""

    # Drop index
    op.drop_index('idx_metrics_player_date', table_name='player_metrics_daily')

    # Drop table
    op.drop_table('player_metrics_daily')

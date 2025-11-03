"""add_player_alerts_table

Revision ID: c92bc516078c
Revises: 379a71045fcf
Create Date: 2025-10-28 13:26:04.555804

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c92bc516078c'
down_revision = '379a71045fcf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add player_alerts table for tracking risk alerts and notifications."""

    # Create player_alerts table
    op.create_table(
        'player_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('level', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for efficient queries
    op.create_index(
        'idx_alerts_player_date',
        'player_alerts',
        ['player_id', sa.text('date DESC')],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove player_alerts table."""

    # Drop index
    op.drop_index('idx_alerts_player_date', table_name='player_alerts')

    # Drop table
    op.drop_table('player_alerts')

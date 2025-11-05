"""add_unique_constraints_for_players

Revision ID: 2e2270ca0b2f
Revises: 26557e0037df
Create Date: 2025-11-05 09:47:46.101659

Adds external_id field and unique constraints for idempotent player seeding:
- external_id: optional external identifier for integration
- Unique constraint on external_id (when NOT NULL)
- Unique constraint on (organization_id, team_id, jersey_number) when jersey_number is NOT NULL
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '2e2270ca0b2f'
down_revision = '26557e0037df'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add external_id column to players table
    op.add_column(
        'players',
        sa.Column('external_id', sa.String(length=255), nullable=True)
    )

    # Create index on external_id for fast lookups
    op.create_index(
        'ix_players_external_id',
        'players',
        ['external_id'],
        unique=False
    )

    # Create partial unique index on external_id (only when NOT NULL)
    # This allows multiple NULL values but enforces uniqueness for non-NULL values
    op.create_index(
        'uq_players_external_id',
        'players',
        ['external_id'],
        unique=True,
        postgresql_where=sa.text('external_id IS NOT NULL')
    )

    # Create partial unique index on (organization_id, team_id, jersey_number)
    # Only enforces uniqueness when jersey_number is NOT NULL
    # This allows players without jersey numbers while preventing duplicates
    op.create_index(
        'uq_players_org_team_jersey',
        'players',
        ['organization_id', 'team_id', 'jersey_number'],
        unique=True,
        postgresql_where=sa.text('jersey_number IS NOT NULL')
    )


def downgrade() -> None:
    # Drop unique indexes
    op.drop_index('uq_players_org_team_jersey', table_name='players')
    op.drop_index('uq_players_external_id', table_name='players')

    # Drop regular index
    op.drop_index('ix_players_external_id', table_name='players')

    # Drop external_id column
    op.drop_column('players', 'external_id')

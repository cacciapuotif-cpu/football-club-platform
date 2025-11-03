"""add_player_session_rpe_tracking

Revision ID: df22d5bc8656
Revises: 45fb13bbe986
Create Date: 2025-10-28 10:20:00.397431

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'df22d5bc8656'
down_revision = '45fb13bbe986'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add player_session table for RPE tracking and session load calculation."""

    # 1. Create player_session table
    op.create_table(
        'player_session',
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rpe', sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column('session_load', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('player_id', 'session_id')
    )

    # 2. Add RPE range constraint
    op.execute("""
        ALTER TABLE player_session
        ADD CONSTRAINT chk_rpe_range
        CHECK (rpe IS NULL OR (rpe >= 0 AND rpe <= 10))
    """)

    # 3. Create indexes for performance
    op.create_index('idx_ps_player', 'player_session', ['player_id'])
    op.create_index('idx_ps_session', 'player_session', ['session_id'])

    # 4. Create weekly load aggregation view
    op.execute("""
        CREATE OR REPLACE VIEW vw_player_weekly_load AS
        SELECT
            ps.player_id,
            date_trunc('week', ts.session_date)::date AS week_start,
            SUM(COALESCE(ps.session_load, 0)) AS weekly_load
        FROM player_session ps
        JOIN training_sessions ts ON ts.id = ps.session_id
        GROUP BY ps.player_id, date_trunc('week', ts.session_date)::date
    """)


def downgrade() -> None:
    """Remove player_session table and related objects."""

    # Drop view
    op.execute('DROP VIEW IF EXISTS vw_player_weekly_load')

    # Drop indexes
    op.drop_index('idx_ps_session', table_name='player_session')
    op.drop_index('idx_ps_player', table_name='player_session')

    # Drop constraint (will be dropped with table, but explicit for clarity)
    op.drop_constraint('chk_rpe_range', 'player_session', type_='check')

    # Drop table
    op.drop_table('player_session')

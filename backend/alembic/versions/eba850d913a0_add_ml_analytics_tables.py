"""add_ml_analytics_tables

Revision ID: eba850d913a0
Revises: e1f2a3b4c5d6
Create Date: 2025-11-03 14:21:42.395090

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'eba850d913a0'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # matches
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('opponent', sa.String(100), nullable=True),
        sa.Column('competition', sa.String(100), nullable=True),
        sa.Column('home', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('minutes', sa.Integer(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_matches_organization_id', 'matches', ['organization_id'])
    op.create_index('ix_matches_date', 'matches', ['date'])

    # training_sessions
    op.create_table(
        'training_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('session_type', sa.String(50), nullable=True),
        sa.Column('duration_min', sa.Integer(), nullable=True),
        sa.Column('rpe', sa.Float(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_sessions_organization_id', 'training_sessions', ['organization_id'])
    op.create_index('ix_training_sessions_date', 'training_sessions', ['date'])

    # player_match_stats
    op.create_table(
        'player_match_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=True),
        sa.Column('goals', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('shots', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('xg', sa.Float(), nullable=True, server_default='0'),
        sa.Column('key_passes', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duels_won', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('sprints', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('pressures', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('def_actions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'match_id', name='uq_player_match')
    )
    op.create_index('ix_player_match_stats_player_id', 'player_match_stats', ['player_id'])
    op.create_index('ix_player_match_stats_match_id', 'player_match_stats', ['match_id'])

    # player_training_load
    op.create_table(
        'player_training_load',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('load_acute', sa.Float(), nullable=True),
        sa.Column('load_chronic', sa.Float(), nullable=True),
        sa.Column('monotony', sa.Float(), nullable=True),
        sa.Column('strain', sa.Float(), nullable=True),
        sa.Column('injury_history_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'session_id', name='uq_player_session')
    )
    op.create_index('ix_player_training_load_player_id', 'player_training_load', ['player_id'])
    op.create_index('ix_player_training_load_session_id', 'player_training_load', ['session_id'])

    # player_features_daily
    op.create_table(
        'player_features_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('rolling_7d_load', sa.Float(), nullable=True),
        sa.Column('rolling_21d_load', sa.Float(), nullable=True),
        sa.Column('form_score', sa.Float(), nullable=True),
        sa.Column('injury_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'date', name='uq_player_date')
    )
    op.create_index('ix_player_features_daily_player_id', 'player_features_daily', ['player_id'])
    op.create_index('ix_player_features_daily_date', 'player_features_daily', ['date'])

    # player_predictions
    op.create_table(
        'player_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('target', sa.String(50), nullable=False),  # 'injury_risk' | 'performance_index'
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('y_pred', sa.Float(), nullable=True),
        sa.Column('y_proba', sa.Float(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'date', 'target', name='uq_player_date_target')
    )
    op.create_index('ix_player_predictions_player_id', 'player_predictions', ['player_id'])
    op.create_index('ix_player_predictions_date', 'player_predictions', ['date'])


def downgrade() -> None:
    op.drop_table('player_predictions')
    op.drop_table('player_features_daily')
    op.drop_table('player_training_load')
    op.drop_table('player_match_stats')
    op.drop_table('training_sessions')
    op.drop_table('matches')

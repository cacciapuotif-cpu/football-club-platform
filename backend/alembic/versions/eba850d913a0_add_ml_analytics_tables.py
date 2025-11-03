"""add_ml_analytics_tables

Revision ID: eba850d913a0
Revises: e5d9f8c7a3b1
Create Date: 2025-11-03 14:21:42.395090

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'eba850d913a0'
down_revision = 'e5d9f8c7a3b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # matches
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('opponent', sa.String(100)),
        sa.Column('competition', sa.String(100)),
        sa.Column('home', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('minutes', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_matches_organization_id', 'matches', ['organization_id'])

    # training_sessions
    op.create_table(
        'training_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('session_type', sa.String(50)),
        sa.Column('duration_min', sa.Integer()),
        sa.Column('rpe', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_training_sessions_organization_id', 'training_sessions', ['organization_id'])

    # player_match_stats
    op.create_table(
        'player_match_stats',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('minutes', sa.Integer()),
        sa.Column('goals', sa.Integer(), server_default='0'),
        sa.Column('assists', sa.Integer(), server_default='0'),
        sa.Column('shots', sa.Integer(), server_default='0'),
        sa.Column('xg', sa.Float(), server_default='0'),
        sa.Column('key_passes', sa.Integer(), server_default='0'),
        sa.Column('duels_won', sa.Integer(), server_default='0'),
        sa.Column('sprints', sa.Integer(), server_default='0'),
        sa.Column('pressures', sa.Integer(), server_default='0'),
        sa.Column('def_actions', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('player_id', 'match_id', name='uq_player_match')
    )
    op.create_index('ix_player_match_stats_player_id', 'player_match_stats', ['player_id'])
    op.create_index('ix_player_match_stats_match_id', 'player_match_stats', ['match_id'])

    # player_training_load
    op.create_table(
        'player_training_load',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('training_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('load_acute', sa.Float()),
        sa.Column('load_chronic', sa.Float()),
        sa.Column('monotony', sa.Float()),
        sa.Column('strain', sa.Float()),
        sa.Column('injury_history_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('player_id', 'session_id', name='uq_player_session')
    )
    op.create_index('ix_player_training_load_player_id', 'player_training_load', ['player_id'])
    op.create_index('ix_player_training_load_session_id', 'player_training_load', ['session_id'])

    # player_features_daily
    op.create_table(
        'player_features_daily',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('rolling_7d_load', sa.Float()),
        sa.Column('rolling_21d_load', sa.Float()),
        sa.Column('form_score', sa.Float()),
        sa.Column('injury_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('player_id', 'date', name='uq_player_date')
    )
    op.create_index('ix_player_features_daily_player_id', 'player_features_daily', ['player_id'])
    op.create_index('ix_player_features_daily_date', 'player_features_daily', ['date'])

    # player_predictions
    op.create_table(
        'player_predictions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('target', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('y_pred', sa.Float()),
        sa.Column('y_proba', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
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

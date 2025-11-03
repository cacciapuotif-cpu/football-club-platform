"""add_advanced_analytics_models

Revision ID: e5d9f8c7a3b1
Revises: 8b99337b804d
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5d9f8c7a3b1'
down_revision: Union[str, None] = '8b99337b804d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Add new columns to players table ###
    op.add_column('players', sa.Column('market_value_eur', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('contract_expiry_date', sa.Date(), nullable=True))
    op.add_column('players', sa.Column('overall_rating', sa.Float(), nullable=True, server_default='6.0'))
    op.add_column('players', sa.Column('potential_rating', sa.Float(), nullable=True, server_default='6.0'))
    op.add_column('players', sa.Column('form_level', sa.Float(), nullable=True, server_default='5.0'))

    # ### Create player_stats table ###
    op.create_table(
        'player_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('season', sa.String(length=20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('minutes_played', sa.Integer(), nullable=False, server_default='0'),

        # Offensive stats
        sa.Column('goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shots', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shots_on_target', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dribbles_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dribbles_success', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('offsides', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('penalties_scored', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('penalties_missed', sa.Integer(), nullable=False, server_default='0'),

        # Passing stats
        sa.Column('passes_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passes_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('key_passes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('through_balls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('crosses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cross_accuracy_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('long_balls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('long_balls_completed', sa.Integer(), nullable=False, server_default='0'),

        # Defensive stats
        sa.Column('tackles_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tackles_success', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interceptions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clearances', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blocks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('aerial_duels_won', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('aerial_duels_lost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duels_won', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duels_lost', sa.Integer(), nullable=False, server_default='0'),

        # Goalkeeper stats
        sa.Column('saves', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('saves_from_inside_box', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('punches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('catches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sweeper_clearances', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('throw_outs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('goal_kicks', sa.Integer(), nullable=False, server_default='0'),

        # Physical & discipline
        sa.Column('distance_covered_m', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sprints', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('top_speed_kmh', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fouls_committed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fouls_suffered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yellow_cards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('red_cards', sa.Integer(), nullable=False, server_default='0'),

        # ML computed metrics
        sa.Column('performance_index', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('influence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_goals_xg', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_assists_xa', sa.Float(), nullable=False, server_default='0.0'),

        # Calculated efficiency percentages
        sa.Column('pass_accuracy_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('shot_accuracy_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tackle_success_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('dribble_success_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('aerial_duel_success_pct', sa.Float(), nullable=False, server_default='0.0'),

        # Metadata
        sa.Column('is_starter', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('substituted_in_minute', sa.Integer(), nullable=True),
        sa.Column('substituted_out_minute', sa.Integer(), nullable=True),

        # Multi-tenancy
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Constraints
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create indexes for player_stats ###
    op.create_index('idx_player_stats_player_season', 'player_stats', ['player_id', 'season'])
    op.create_index('idx_player_stats_player_date', 'player_stats', ['player_id', 'date'])
    op.create_index('idx_player_stats_org_date', 'player_stats', ['organization_id', 'date'])
    op.create_index(op.f('ix_player_stats_player_id'), 'player_stats', ['player_id'])
    op.create_index(op.f('ix_player_stats_match_id'), 'player_stats', ['match_id'])
    op.create_index(op.f('ix_player_stats_session_id'), 'player_stats', ['session_id'])
    op.create_index(op.f('ix_player_stats_season'), 'player_stats', ['season'])
    op.create_index(op.f('ix_player_stats_organization_id'), 'player_stats', ['organization_id'])


def downgrade() -> None:
    # ### Drop player_stats table and indexes ###
    op.drop_index(op.f('ix_player_stats_organization_id'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_season'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_session_id'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_match_id'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_player_id'), table_name='player_stats')
    op.drop_index('idx_player_stats_org_date', table_name='player_stats')
    op.drop_index('idx_player_stats_player_date', table_name='player_stats')
    op.drop_index('idx_player_stats_player_season', table_name='player_stats')
    op.drop_table('player_stats')

    # ### Drop columns from players table ###
    op.drop_column('players', 'form_level')
    op.drop_column('players', 'potential_rating')
    op.drop_column('players', 'overall_rating')
    op.drop_column('players', 'contract_expiry_date')
    op.drop_column('players', 'market_value_eur')

"""Add tactical psychological attributes and training stats

Revision ID: e1f2a3b4c5d6
Revises: e5d9f8c7a3b1
Create Date: 2025-11-03 12:00:00

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'e5d9f8c7a3b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to players table
    op.add_column('players', sa.Column('physical_condition', sa.String(length=50), nullable=True, server_default='normal'))
    op.add_column('players', sa.Column('injury_prone', sa.Boolean(), nullable=False, server_default='false'))

    # Tactical attributes
    op.add_column('players', sa.Column('tactical_awareness', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('positioning', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('decision_making', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('work_rate', sa.Integer(), nullable=False, server_default='50'))

    # Psychological attributes
    op.add_column('players', sa.Column('mental_strength', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('leadership', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('concentration', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('players', sa.Column('adaptability', sa.Integer(), nullable=False, server_default='50'))

    # Add new columns to training_sessions table
    op.add_column('training_sessions', sa.Column('focus_area', sa.String(length=255), nullable=True))
    op.add_column('training_sessions', sa.Column('coach_notes', sa.Text(), nullable=True))
    op.add_column('training_sessions', sa.Column('intensity', sa.String(length=10), nullable=True, server_default='MEDIUM'))

    # Create player_training_stats table
    op.create_table(
        'player_training_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('training_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attendance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('participation_pct', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('late_arrival_min', sa.Integer(), nullable=False, server_default='0'),

        # Technical ratings (1-10)
        sa.Column('technical_rating', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('tactical_execution', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('physical_performance', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('mental_focus', sa.Integer(), nullable=False, server_default='5'),

        # Technical metrics
        sa.Column('passing_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('shooting_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('dribbling_success', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_touch_quality', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('defensive_actions', sa.Integer(), nullable=False, server_default='0'),

        # Physical metrics
        sa.Column('speed_kmh', sa.Float(), nullable=True),
        sa.Column('endurance_index', sa.Float(), nullable=True),
        sa.Column('recovery_rate', sa.Float(), nullable=True),
        sa.Column('distance_covered_m', sa.Float(), nullable=True),
        sa.Column('hi_intensity_runs', sa.Integer(), nullable=True),
        sa.Column('sprints_count', sa.Integer(), nullable=True),

        # Fitness & conditioning
        sa.Column('aerobic_capacity', sa.Float(), nullable=True),
        sa.Column('power_output', sa.Float(), nullable=True),
        sa.Column('agility_score', sa.Float(), nullable=True),
        sa.Column('strength_score', sa.Float(), nullable=True),

        # Wellness & RPE
        sa.Column('rpe_score', sa.Integer(), nullable=True),
        sa.Column('fatigue_level', sa.Integer(), nullable=True),
        sa.Column('muscle_soreness', sa.Integer(), nullable=True),
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        sa.Column('hydration_level', sa.Integer(), nullable=True),

        # Coach feedback
        sa.Column('coach_feedback', sa.Text(), nullable=True),
        sa.Column('areas_to_improve', sa.Text(), nullable=True),
        sa.Column('positive_notes', sa.Text(), nullable=True),
        sa.Column('attitude_rating', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('teamwork_rating', sa.Integer(), nullable=False, server_default='5'),

        # Injury monitoring
        sa.Column('injury_concern', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('injury_notes', sa.String(length=500), nullable=True),
        sa.Column('recommended_rest', sa.Boolean(), nullable=False, server_default='false'),

        # ML computed
        sa.Column('training_load_score', sa.Float(), nullable=True),
        sa.Column('performance_trend', sa.String(length=20), nullable=True),
        sa.Column('predicted_match_readiness', sa.Float(), nullable=True),

        # Metadata
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Constraints
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['training_session_id'], ['training_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_player_training_player_session', 'player_training_stats', ['player_id', 'training_session_id'], unique=False)
    op.create_index('idx_player_training_org', 'player_training_stats', ['organization_id'], unique=False)
    op.create_index(op.f('ix_player_training_stats_player_id'), 'player_training_stats', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_training_stats_training_session_id'), 'player_training_stats', ['training_session_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_player_training_org', table_name='player_training_stats')
    op.drop_index('idx_player_training_player_session', table_name='player_training_stats')
    op.drop_index(op.f('ix_player_training_stats_training_session_id'), table_name='player_training_stats')
    op.drop_index(op.f('ix_player_training_stats_player_id'), table_name='player_training_stats')

    # Drop table
    op.drop_table('player_training_stats')

    # Remove columns from training_sessions
    op.drop_column('training_sessions', 'intensity')
    op.drop_column('training_sessions', 'coach_notes')
    op.drop_column('training_sessions', 'focus_area')

    # Remove columns from players
    op.drop_column('players', 'adaptability')
    op.drop_column('players', 'concentration')
    op.drop_column('players', 'leadership')
    op.drop_column('players', 'mental_strength')
    op.drop_column('players', 'work_rate')
    op.drop_column('players', 'decision_making')
    op.drop_column('players', 'positioning')
    op.drop_column('players', 'tactical_awareness')
    op.drop_column('players', 'injury_prone')
    op.drop_column('players', 'physical_condition')

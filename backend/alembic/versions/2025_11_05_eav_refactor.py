"""Add EAV models for flexible metrics tracking

Revision ID: 2025_11_05_eav
Revises: 2e2270ca0b2f
Create Date: 2025-11-05

Adds new EAV (Entity-Attribute-Value) tables for flexible metric storage:
- wellness_sessions + wellness_metrics (replaces flat wellness_data)
- training_attendance + training_metrics (extends training_sessions)
- match_metrics + match_player_positions (extends attendances)
- metric_catalog + data_quality_logs (metadata and validation)
- data_completeness (rollup for dashboards)

Also creates materialized views for performance.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_11_05_eav'
down_revision = '2e2270ca0b2f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # WELLNESS EAV
    # =========================================================================
    op.create_table(
        'wellness_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('schema_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('note', sa.String(500), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_wellness_session_player_date', 'wellness_sessions', ['player_id', 'date'])
    # UNIQUE: one session per player per date
    op.create_unique_constraint('uix_wellness_sessions_player_date', 'wellness_sessions', ['player_id', 'date'])

    op.create_table(
        'wellness_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('wellness_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wellness_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('metric_key', sa.String(100), nullable=False, index=True),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('validity', sa.String(20), nullable=False, server_default='valid'),
        sa.Column('tags', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_wellness_metric_session_key', 'wellness_metrics', ['wellness_session_id', 'metric_key'])
    op.create_index('idx_wellness_metric_key_value', 'wellness_metrics', ['metric_key', 'metric_value'])

    # =========================================================================
    # TRAINING EAV
    # =========================================================================
    op.create_table(
        'training_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('training_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='present'),
        sa.Column('minutes', sa.Integer(), nullable=True),
        sa.Column('participation_pct', sa.Integer(), nullable=True),
        sa.Column('rpe_post', sa.Integer(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_training_attendance_session_player', 'training_attendance', ['training_session_id', 'player_id'])
    # UNIQUE: one attendance per player per training session
    op.create_unique_constraint('uix_training_attendance_session_player', 'training_attendance', ['training_session_id', 'player_id'])

    op.create_table(
        'training_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('training_attendance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_attendance.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('metric_key', sa.String(100), nullable=False, index=True),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('validity', sa.String(20), nullable=False, server_default='valid'),
        sa.Column('tags', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_training_metric_attendance_key', 'training_metrics', ['training_attendance_id', 'metric_key'])
    op.create_index('idx_training_metric_key_value', 'training_metrics', ['metric_key', 'metric_value'])

    # =========================================================================
    # MATCH EAV
    # =========================================================================
    op.create_table(
        'match_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attendance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attendances.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('metric_key', sa.String(100), nullable=False, index=True),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('validity', sa.String(20), nullable=False, server_default='valid'),
        sa.Column('tags', sa.String(200), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_match_metric_attendance_key', 'match_metrics', ['attendance_id', 'metric_key'])
    op.create_index('idx_match_metric_key_value', 'match_metrics', ['metric_key', 'metric_value'])

    op.create_table(
        'match_player_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attendance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attendances.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('position', sa.String(20), nullable=False),
        sa.Column('minute_start', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('minute_end', sa.Integer(), nullable=True),
        sa.Column('formation_position', sa.String(50), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # =========================================================================
    # CATALOG & DATA QUALITY
    # =========================================================================
    op.create_table(
        'metric_catalog',
        sa.Column('metric_key', sa.String(100), primary_key=True),
        sa.Column('area', sa.String(50), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('unit_default', sa.String(50), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('direction', sa.String(50), nullable=True),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('display_format', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replacement_key', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'data_quality_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_type', sa.String(100), nullable=False),
        sa.Column('issue_details', sa.String(500), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.String(500), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_dq_entity_type_id', 'data_quality_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_dq_severity_resolved', 'data_quality_logs', ['severity', 'resolved'])
    op.create_index('idx_dq_detected_at', 'data_quality_logs', ['detected_at'])

    op.create_table(
        'data_completeness',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, index=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('wellness_completeness', sa.Float(), nullable=False, server_default='0'),
        sa.Column('training_completeness', sa.Float(), nullable=False, server_default='0'),
        sa.Column('match_completeness', sa.Float(), nullable=False, server_default='0'),
        sa.Column('wellness_metrics_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('training_sessions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matches_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_completeness_player_date', 'data_completeness', ['player_id', 'date'])

    # =========================================================================
    # MATERIALIZED VIEWS (for performance)
    # =========================================================================
    # Wellness timeseries view
    op.execute("""
        CREATE VIEW mv_wellness_timeseries AS
        SELECT
            ws.player_id,
            ws.date,
            wm.metric_key,
            wm.metric_value,
            wm.unit
        FROM wellness_sessions ws
        JOIN wellness_metrics wm ON wm.wellness_session_id = ws.id
        WHERE wm.validity = 'valid'
    """)

    # Training load view with sRPE and ACWR
    op.execute("""
        CREATE VIEW mv_training_load AS
        SELECT
            ta.player_id,
            ts.session_date::date AS date,
            ta.minutes,
            COALESCE(ta.rpe_post, 0) * COALESCE(ta.minutes, 0) AS srpe,
            MAX(CASE WHEN tm.metric_key='hsr' THEN tm.metric_value END) AS hsr,
            MAX(CASE WHEN tm.metric_key='total_distance' THEN tm.metric_value END) AS total_distance
        FROM training_attendance ta
        JOIN training_sessions ts ON ts.id = ta.training_session_id
        LEFT JOIN training_metrics tm ON tm.training_attendance_id = ta.id
        GROUP BY ta.player_id, ts.session_date::date, ta.minutes, ta.rpe_post
    """)

    # Seed metric catalog with common metrics
    op.execute("""
        INSERT INTO metric_catalog (metric_key, area, description, unit_default, min_value, max_value, direction, display_name) VALUES
        -- Wellness
        ('sleep_quality', 'wellness', 'Sleep quality (1-10)', 'score', 1, 10, 'up_is_better', 'Sleep Quality'),
        ('sleep_hours', 'wellness', 'Hours of sleep', 'hours', 0, 24, 'up_is_better', 'Sleep Hours'),
        ('stress', 'wellness', 'Stress level (1-10)', 'score', 1, 10, 'down_is_better', 'Stress'),
        ('fatigue', 'wellness', 'Fatigue level (1-10)', 'score', 1, 10, 'down_is_better', 'Fatigue'),
        ('doms', 'wellness', 'Delayed Onset Muscle Soreness (1-10)', 'score', 1, 10, 'down_is_better', 'DOMS'),
        ('mood', 'wellness', 'Mood (1-10)', 'score', 1, 10, 'up_is_better', 'Mood'),
        ('motivation', 'wellness', 'Motivation (1-10)', 'score', 1, 10, 'up_is_better', 'Motivation'),
        ('hydration', 'wellness', 'Hydration (1-10)', 'score', 1, 10, 'up_is_better', 'Hydration'),
        ('rpe_morning', 'wellness', 'Morning RPE (1-10)', 'score', 1, 10, 'down_is_better', 'Morning RPE'),
        ('body_weight_kg', 'wellness', 'Body weight', 'kg', 30, 150, 'neutral', 'Weight'),
        ('resting_hr_bpm', 'wellness', 'Resting heart rate', 'bpm', 30, 120, 'down_is_better', 'Resting HR'),
        ('hrv_ms', 'wellness', 'Heart rate variability', 'ms', 0, 300, 'up_is_better', 'HRV'),

        -- Training
        ('rpe_post', 'training', 'Session RPE (1-10)', 'score', 1, 10, 'neutral', 'RPE'),
        ('hsr', 'training', 'High Speed Running', 'm', 0, 5000, 'up_is_better', 'HSR'),
        ('sprint_count', 'training', 'Number of sprints', '#', 0, 200, 'neutral', 'Sprints'),
        ('total_distance', 'training', 'Total distance', 'km', 0, 20, 'up_is_better', 'Distance'),
        ('accel_count', 'training', 'Accelerations', '#', 0, 400, 'neutral', 'Accelerations'),
        ('decel_count', 'training', 'Decelerations', '#', 0, 400, 'neutral', 'Decelerations'),
        ('top_speed', 'training', 'Top speed', 'km/h', 0, 40, 'up_is_better', 'Top Speed'),
        ('avg_hr', 'training', 'Average heart rate', 'bpm', 60, 220, 'neutral', 'Avg HR'),
        ('max_hr', 'training', 'Maximum heart rate', 'bpm', 60, 220, 'neutral', 'Max HR'),
        ('player_load', 'training', 'Player load', 'AU', 0, 1000, 'neutral', 'Player Load'),

        -- Match
        ('pass_accuracy', 'match', 'Pass accuracy', '%', 0, 100, 'up_is_better', 'Pass Accuracy'),
        ('pass_completed', 'match', 'Passes completed', '#', 0, 200, 'up_is_better', 'Passes'),
        ('duels_won', 'match', 'Duels won', '#', 0, 100, 'up_is_better', 'Duels Won'),
        ('touches', 'match', 'Number of touches', '#', 0, 300, 'neutral', 'Touches'),
        ('dribbles_success', 'match', 'Successful dribbles', '#', 0, 50, 'up_is_better', 'Dribbles'),
        ('interceptions', 'match', 'Interceptions', '#', 0, 50, 'up_is_better', 'Interceptions'),
        ('tackles', 'match', 'Tackles', '#', 0, 50, 'up_is_better', 'Tackles'),
        ('shots_on_target', 'match', 'Shots on target', '#', 0, 20, 'up_is_better', 'Shots on Target')
    """)


def downgrade() -> None:
    # Drop views first
    op.execute("DROP VIEW IF EXISTS mv_training_load")
    op.execute("DROP VIEW IF EXISTS mv_wellness_timeseries")

    # Drop tables in reverse order
    op.drop_table('data_completeness')
    op.drop_table('data_quality_logs')
    op.drop_table('metric_catalog')
    op.drop_table('match_player_positions')
    op.drop_table('match_metrics')
    op.drop_table('training_metrics')
    op.drop_table('training_attendance')
    op.drop_table('wellness_metrics')
    op.drop_table('wellness_sessions')

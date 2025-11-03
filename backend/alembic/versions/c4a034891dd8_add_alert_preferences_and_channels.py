"""add_alert_preferences_and_channels

Revision ID: c4a034891dd8
Revises: c92bc516078c
Create Date: 2025-10-28 19:09:36.798866

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'c4a034891dd8'
down_revision = 'c92bc516078c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add alert preferences, channels, push subscriptions and monthly history view."""

    # Create alert_preferences table
    op.create_table(
        'alert_preferences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=True),
        sa.Column('player_id', sa.UUID(), nullable=True),
        sa.Column('metric', sa.Text(), nullable=False),
        sa.Column('threshold_min', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('threshold_max', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('level', sa.Text(), server_default='warning', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_pref_player', 'alert_preferences', ['player_id'])

    # Create alert_channels table
    op.create_table(
        'alert_channels',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=True),
        sa.Column('player_id', sa.UUID(), nullable=True),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_channels_player', 'alert_channels', ['player_id'])

    # Create push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.Text(), nullable=False),
        sa.Column('auth', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_push_subscriptions_user', 'push_subscriptions', ['user_id'])
    op.create_index('idx_push_subscriptions_endpoint', 'push_subscriptions', ['endpoint'], unique=True)

    # Create vw_alerts_monthly view
    op.execute("""
        CREATE OR REPLACE VIEW vw_alerts_monthly AS
        SELECT
            player_id,
            date_trunc('month', date)::date AS month_start,
            type,
            level,
            COUNT(*) AS count_alerts
        FROM player_alerts
        GROUP BY player_id, date_trunc('month', date), type, level
    """)


def downgrade() -> None:
    """Remove alert preferences, channels, push subscriptions and monthly history view."""

    # Drop view
    op.execute('DROP VIEW IF EXISTS vw_alerts_monthly')

    # Drop push_subscriptions table
    op.drop_index('idx_push_subscriptions_endpoint', table_name='push_subscriptions')
    op.drop_index('idx_push_subscriptions_user', table_name='push_subscriptions')
    op.drop_table('push_subscriptions')

    # Drop alert_channels table
    op.drop_index('idx_alert_channels_player', table_name='alert_channels')
    op.drop_table('alert_channels')

    # Drop alert_preferences table
    op.drop_index('idx_alert_pref_player', table_name='alert_preferences')
    op.drop_table('alert_preferences')

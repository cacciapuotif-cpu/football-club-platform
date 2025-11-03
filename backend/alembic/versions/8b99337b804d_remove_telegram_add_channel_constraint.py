"""remove_telegram_add_channel_constraint

Revision ID: 8b99337b804d
Revises: c4a034891dd8
Create Date: 2025-10-28 19:26:45.552720

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '8b99337b804d'
down_revision = 'c4a034891dd8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove Telegram support and add CHECK constraint for alert_channels."""

    # Delete any existing Telegram channels (if any)
    op.execute("DELETE FROM alert_channels WHERE channel = 'telegram'")

    # Add CHECK constraint to allow only 'email' and 'webpush'
    op.execute("""
        ALTER TABLE alert_channels
        ADD CONSTRAINT chk_alert_channels_type
        CHECK (channel IN ('email', 'webpush'))
    """)


def downgrade() -> None:
    """Remove CHECK constraint to allow Telegram again."""

    # Drop the CHECK constraint
    op.execute("ALTER TABLE alert_channels DROP CONSTRAINT IF EXISTS chk_alert_channels_type")

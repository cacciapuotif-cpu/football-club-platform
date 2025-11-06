"""add_complete_metric_catalog

Revision ID: ad129d225dab
Revises: 2025_11_05_eav
Create Date: 2025-11-06 12:19:35.869077

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'ad129d225dab'
down_revision = '2025_11_05_eav'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing metrics to set family = area
    op.execute("""
        UPDATE metric_catalog
        SET family = area
        WHERE family IS NULL
    """)
    
    # Add missing wellness metrics
    op.execute("""
        INSERT INTO metric_catalog (metric_key, area, family, description, unit_default, min_value, max_value, direction, display_name)
        VALUES
        ('soreness', 'wellness', 'wellness', 'Muscle soreness (1-10)', 'score', 1, 10, 'down_is_better', 'Soreness')
        ON CONFLICT (metric_key) DO NOTHING
    """)
    
    # Add missing training metrics (already have most, but ensure all are present)
    op.execute("""
        INSERT INTO metric_catalog (metric_key, area, family, description, unit_default, min_value, max_value, direction, display_name)
        VALUES
        ('player_load', 'training', 'training', 'Player load (arbitrary units)', 'AU', 0, 1000, 'neutral', 'Player Load')
        ON CONFLICT (metric_key) DO UPDATE SET family = 'training'
    """)
    
    # Add missing match metrics
    op.execute("""
        INSERT INTO metric_catalog (metric_key, area, family, description, unit_default, min_value, max_value, direction, display_name)
        VALUES
        ('passes_completed', 'match', 'match', 'Passes completed', '#', 0, 200, 'up_is_better', 'Passes Completed')
        ON CONFLICT (metric_key) DO NOTHING
    """)
    
    # Add tactical metrics (placeholder)
    op.execute("""
        INSERT INTO metric_catalog (metric_key, area, family, description, unit_default, min_value, max_value, direction, display_name)
        VALUES
        ('pressures', 'tactical', 'tactical', 'Number of pressures applied', '#', 0, 100, 'up_is_better', 'Pressures'),
        ('recoveries_def_third', 'tactical', 'tactical', 'Ball recoveries in defensive third', '#', 0, 50, 'up_is_better', 'Defensive Recoveries'),
        ('progressive_passes', 'tactical', 'tactical', 'Progressive passes completed', '#', 0, 50, 'up_is_better', 'Progressive Passes'),
        ('line_breaking_passes_conceded', 'tactical', 'tactical', 'Line-breaking passes conceded', '#', 0, 30, 'down_is_better', 'Line Breaks Conceded'),
        ('xthreat_contrib', 'tactical', 'tactical', 'Expected threat contribution', 'score', 0, 5, 'up_is_better', 'xThreat Contribution')
        ON CONFLICT (metric_key) DO NOTHING
    """)


def downgrade() -> None:
    # Remove tactical metrics
    op.execute("""
        DELETE FROM metric_catalog
        WHERE metric_key IN ('pressures', 'recoveries_def_third', 'progressive_passes', 
                             'line_breaking_passes_conceded', 'xthreat_contrib')
    """)
    
    # Remove soreness if it was added
    op.execute("""
        DELETE FROM metric_catalog WHERE metric_key = 'soreness'
    """)

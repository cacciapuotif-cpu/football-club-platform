"""add_wellness_summary_view_and_indexes

Revision ID: 45fb13bbe986
Revises: 66a6bcbaa092
Create Date: 2025-10-28 09:58:04.172215

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '45fb13bbe986'
down_revision = '66a6bcbaa092'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes, wellness summary view, and data constraints."""

    # 1. Add indexes for performance
    op.create_index(
        'idx_players_last_name_first_name',
        'players',
        ['last_name', 'first_name'],
        unique=False
    )

    op.create_index(
        'idx_wellness_data_player_date_desc',
        'wellness_data',
        ['player_id', sa.text('date DESC')],
        unique=False,
        postgresql_using='btree'
    )

    # 2. Create wellness summary view with Italian aliases
    # Note: view doesn't filter by date - filtering happens in API layer
    op.execute("""
        CREATE OR REPLACE VIEW vw_wellness_summary AS
        SELECT
            p.id AS player_id,
            p.last_name AS cognome,
            p.first_name AS nome,
            p.role_primary AS ruolo,
            COUNT(w.date) AS wellness_sessions_count,
            MAX(w.date) AS last_entry_date
        FROM players p
        LEFT JOIN wellness_data w ON w.player_id = p.id
        GROUP BY p.id, p.last_name, p.first_name, p.role_primary;
    """)

    # 3. Add check constraints for wellness data ranges
    # Using IF NOT EXISTS pattern to avoid conflicts if constraints exist

    # Sleep hours: 0-24 (some athletes may sleep very long after intense training)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_sleep_hours_range
            CHECK (sleep_hours IS NULL OR (sleep_hours >= 0 AND sleep_hours <= 24));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Sleep quality: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_sleep_quality_range
            CHECK (sleep_quality IS NULL OR (sleep_quality >= 1 AND sleep_quality <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Fatigue rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_fatigue_rating_range
            CHECK (fatigue_rating IS NULL OR (fatigue_rating >= 1 AND fatigue_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Stress rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_stress_rating_range
            CHECK (stress_rating IS NULL OR (stress_rating >= 1 AND stress_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Mood rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_mood_rating_range
            CHECK (mood_rating IS NULL OR (mood_rating >= 1 AND mood_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # DOMS rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_doms_rating_range
            CHECK (doms_rating IS NULL OR (doms_rating >= 1 AND doms_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Motivation rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_motivation_rating_range
            CHECK (motivation_rating IS NULL OR (motivation_rating >= 1 AND motivation_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Hydration rating: 1-5 scale
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_hydration_rating_range
            CHECK (hydration_rating IS NULL OR (hydration_rating >= 1 AND hydration_rating <= 5));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Body weight: reasonable range 40-150kg
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_body_weight_range
            CHECK (body_weight_kg IS NULL OR (body_weight_kg >= 40 AND body_weight_kg <= 150));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # HRV: positive values only (ms)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_hrv_positive
            CHECK (hrv_ms IS NULL OR hrv_ms >= 0);
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # Resting HR: reasonable range 30-120 bpm
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE wellness_data
            ADD CONSTRAINT chk_resting_hr_range
            CHECK (resting_hr_bpm IS NULL OR (resting_hr_bpm >= 30 AND resting_hr_bpm <= 120));
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)


def downgrade() -> None:
    """Remove indexes, view, and constraints."""

    # Drop check constraints
    op.drop_constraint('chk_sleep_hours_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_sleep_quality_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_fatigue_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_stress_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_mood_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_doms_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_motivation_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_hydration_rating_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_body_weight_range', 'wellness_data', type_='check')
    op.drop_constraint('chk_hrv_positive', 'wellness_data', type_='check')
    op.drop_constraint('chk_resting_hr_range', 'wellness_data', type_='check')

    # Drop view
    op.execute('DROP VIEW IF EXISTS vw_wellness_summary;')

    # Drop indexes
    op.drop_index('idx_wellness_data_player_date_desc', table_name='wellness_data')
    op.drop_index('idx_players_last_name_first_name', table_name='players')

"""Introduce core sessions & wellness tables with RLS."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2025_11_08_a1_sessions_wellness"
down_revision: str = "2025_11_05_eav"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athletes",
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("pii_token", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_athletes_tenant_status", "athletes", ["tenant_id", "status"])

    op.create_table(
        "sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False, index=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rpe_avg", sa.Numeric(6, 2), nullable=True),
        sa.Column("load", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sessions_tenant_team_start", "sessions", ["tenant_id", "team_id", "start_ts"])

    op.create_table(
        "session_participation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("athletes.athlete_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rpe", sa.Numeric(5, 2), nullable=True),
        sa.Column("load", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint(
        "uix_session_participation_session_athlete",
        "session_participation",
        ["tenant_id", "session_id", "athlete_id"],
    )

    op.create_table(
        "wellness_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("athletes.athlete_id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("metric", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ingest_ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("quality_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_wellness_readings_metric", "wellness_readings", ["tenant_id", "metric", "event_ts"])

    op.create_table(
        "features",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_name", sa.String(length=120), nullable=False),
        sa.Column("feature_value", sa.Numeric(14, 6), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "athlete_id", "feature_name", "event_ts", name="pk_features"),
    )
    op.create_index("idx_features_latest", "features", ["tenant_id", "athlete_id", "event_ts"])

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("athletes.athlete_id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("drivers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_predictions_tenant_athlete_event", "predictions", ["tenant_id", "athlete_id", "event_ts"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("athletes.athlete_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.session_id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("policy_id", sa.String(length=50), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ack_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_alerts_tenant_status", "alerts", ["tenant_id", "status", "severity"])

    # Enable RLS and define tenant isolation policies.
    for table_name in [
        "athletes",
        "sessions",
        "session_participation",
        "wellness_readings",
        "features",
        "predictions",
        "alerts",
    ]:
        op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(
                f"""
                CREATE POLICY {table_name}_tenant_isolation ON {table_name}
                FOR ALL
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
                WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
                """
            )
        )


def downgrade() -> None:
    for table_name in [
        "alerts",
        "predictions",
        "features",
        "wellness_readings",
        "session_participation",
        "sessions",
        "athletes",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name}"))
        op.execute(sa.text(f"ALTER TABLE IF EXISTS {table_name} DISABLE ROW LEVEL SECURITY"))

    op.drop_index("idx_alerts_tenant_status", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("idx_predictions_tenant_athlete_event", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("idx_features_latest", table_name="features")
    op.drop_table("features")

    op.drop_index("idx_wellness_readings_metric", table_name="wellness_readings")
    op.drop_table("wellness_readings")

    op.drop_constraint("uix_session_participation_session_athlete", "session_participation", type_="unique")
    op.drop_table("session_participation")

    op.drop_index("idx_sessions_tenant_team_start", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("idx_athletes_tenant_status", table_name="athletes")
    op.drop_table("athletes")


"""V007 — Advanced Health Engines : Digital Twin V2, Biological Age, Motion Intelligence.

Revision: V007
Down-revision: V006

Crée :
  - digital_twin_snapshots
  - biological_age_snapshots
  - motion_intelligence_snapshots

Ajoute index composites sur tables existantes :
  - vision_sessions (user_id, session_date)
  - daily_metrics (user_id, metrics_date)
  - conversation_messages (thread_id, created_at)
  - readiness_scores (user_id, score_date)
  - longevity_scores (user_id, score_date)
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "V007"
down_revision: Union[str, None] = "V006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── digital_twin_snapshots ─────────────────────────────────────────────────
    op.create_table(
        "digital_twin_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_status", sa.String(20), nullable=True),
        sa.Column("primary_concern", sa.Text(), nullable=True),
        sa.Column("global_confidence", sa.Float(), nullable=True),
        sa.Column("plateau_risk", sa.Boolean(), nullable=True),
        sa.Column("under_recovery_risk", sa.Boolean(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("algorithm_version", sa.String(10), server_default="v1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "snapshot_date", name="uq_digital_twin_user_date"),
    )
    op.create_index("ix_digital_twin_user_id", "digital_twin_snapshots", ["user_id"])
    op.create_index("ix_digital_twin_user_date", "digital_twin_snapshots", ["user_id", "snapshot_date"])

    # ── biological_age_snapshots ───────────────────────────────────────────────
    op.create_table(
        "biological_age_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("chronological_age", sa.Integer(), nullable=True),
        sa.Column("biological_age", sa.Float(), nullable=True),
        sa.Column("biological_age_delta", sa.Float(), nullable=True),
        sa.Column("longevity_risk_score", sa.Float(), nullable=True),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("levers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trend_direction", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("algorithm_version", sa.String(10), server_default="v1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "snapshot_date", name="uq_bio_age_user_date"),
    )
    op.create_index("ix_bio_age_user_id", "biological_age_snapshots", ["user_id"])
    op.create_index("ix_bio_age_user_date", "biological_age_snapshots", ["user_id", "snapshot_date"])

    # ── motion_intelligence_snapshots ──────────────────────────────────────────
    op.create_table(
        "motion_intelligence_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("movement_health_score", sa.Float(), nullable=True),
        sa.Column("stability_score", sa.Float(), nullable=True),
        sa.Column("mobility_score", sa.Float(), nullable=True),
        sa.Column("asymmetry_score", sa.Float(), nullable=True),
        sa.Column("overall_quality_trend", sa.String(20), nullable=True),
        sa.Column("consecutive_quality_sessions", sa.Integer(), nullable=True),
        sa.Column("sessions_analyzed", sa.Integer(), nullable=True),
        sa.Column("days_analyzed", sa.Integer(), nullable=True),
        sa.Column("exercise_profiles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_alerts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("algorithm_version", sa.String(10), server_default="v1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "snapshot_date", name="uq_motion_user_date"),
    )
    op.create_index("ix_motion_user_id", "motion_intelligence_snapshots", ["user_id"])
    op.create_index("ix_motion_user_date", "motion_intelligence_snapshots", ["user_id", "snapshot_date"])

    # ── Composite indexes on existing tables (performance) ─────────────────────
    # vision_sessions — already indexed on user_id; add compound for date range queries
    op.create_index(
        "ix_vision_sessions_user_date",
        "vision_sessions",
        ["user_id", "session_date"],
        if_not_exists=True,
    )
    # daily_metrics
    op.create_index(
        "ix_daily_metrics_user_date",
        "daily_metrics",
        ["user_id", "metrics_date"],
        if_not_exists=True,
    )
    # conversation_messages — for fast thread history queries
    op.create_index(
        "ix_conversation_messages_thread_created",
        "conversation_messages",
        ["thread_id", "created_at"],
        if_not_exists=True,
    )
    # readiness_scores
    op.create_index(
        "ix_readiness_scores_user_date",
        "readiness_scores",
        ["user_id", "score_date"],
        if_not_exists=True,
    )
    # longevity_scores
    op.create_index(
        "ix_longevity_scores_user_date",
        "longevity_scores",
        ["user_id", "score_date"],
        if_not_exists=True,
    )


def downgrade() -> None:
    # Remove new indexes on existing tables
    op.drop_index("ix_longevity_scores_user_date", table_name="longevity_scores", if_exists=True)
    op.drop_index("ix_readiness_scores_user_date", table_name="readiness_scores", if_exists=True)
    op.drop_index("ix_conversation_messages_thread_created", table_name="conversation_messages", if_exists=True)
    op.drop_index("ix_daily_metrics_user_date", table_name="daily_metrics", if_exists=True)
    op.drop_index("ix_vision_sessions_user_date", table_name="vision_sessions", if_exists=True)

    # Drop new tables
    op.drop_table("motion_intelligence_snapshots")
    op.drop_table("biological_age_snapshots")
    op.drop_table("digital_twin_snapshots")

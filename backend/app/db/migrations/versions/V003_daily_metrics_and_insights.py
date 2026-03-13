"""
V003 — Daily Metrics Aggregator + Insights Engine (LOT 3)

Crée :
  - daily_metrics : snapshot journalier agrégé (upsert quotidien)
  - insights : insights santé détectés automatiquement

Depends on : V002
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "V003"
down_revision: Union[str, None] = "V002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Table daily_metrics ────────────────────────────────────────────────────
    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("metrics_date", sa.Date(), nullable=False),
        # Corps
        sa.Column("weight_kg", sa.Float(), nullable=True),
        # Nutrition
        sa.Column("calories_consumed", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("calories_target", sa.Float(), nullable=True),
        sa.Column("protein_target_g", sa.Float(), nullable=True),
        sa.Column("meal_count", sa.Integer(), nullable=True),
        # Hydratation
        sa.Column("hydration_ml", sa.Integer(), nullable=True),
        sa.Column("hydration_target_ml", sa.Integer(), nullable=True),
        # Activité
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("active_calories_kcal", sa.Float(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        # Signaux physiologiques
        sa.Column("resting_heart_rate_bpm", sa.Float(), nullable=True),
        sa.Column("hrv_ms", sa.Float(), nullable=True),
        # Sommeil
        sa.Column("sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("sleep_score", sa.Float(), nullable=True),
        sa.Column("sleep_quality_label", sa.String(20), nullable=True),
        # Entraînement
        sa.Column("workout_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tonnage_kg", sa.Float(), nullable=True),
        sa.Column("training_load", sa.Float(), nullable=True),
        # Scores
        sa.Column("readiness_score", sa.Float(), nullable=True),
        sa.Column("longevity_score", sa.Float(), nullable=True),
        # Méta
        sa.Column("data_completeness_pct", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # PK + FK
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Unicité
        sa.UniqueConstraint("user_id", "metrics_date", name="uq_daily_metrics_user_date"),
    )
    op.create_index("ix_daily_metrics_user_id", "daily_metrics", ["user_id"])
    op.create_index("ix_daily_metrics_date", "daily_metrics", ["metrics_date"])
    op.create_index("ix_daily_metrics_user_date", "daily_metrics", ["user_id", "metrics_date"])

    # ── Table insights ─────────────────────────────────────────────────────────
    op.create_table(
        "insights",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("insight_date", sa.Date(), nullable=False),
        # Classification
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        # Contenu
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action", sa.String(500), nullable=True),
        sa.Column("data_evidence", sa.dialects.postgresql.JSONB(), nullable=True),
        # Statut
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_dismissed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # PK + FK
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Anti-doublon
        sa.UniqueConstraint("user_id", "insight_date", "category", "title",
                            name="uq_insight_user_date_category_title"),
    )
    op.create_index("ix_insights_user_id", "insights", ["user_id"])
    op.create_index("ix_insights_date", "insights", ["insight_date"])
    op.create_index("ix_insights_category", "insights", ["category"])
    op.create_index("ix_insights_severity", "insights", ["severity"])
    # Index partiel : insights actifs (non dismissés)
    op.execute(
        "CREATE INDEX ix_insights_active ON insights (user_id, insight_date) "
        "WHERE is_dismissed = FALSE"
    )

    # ── ReadinessScore : ajout updated_at si absent ───────────────────────────
    # Idempotent : si la colonne existe déjà (ajoutée par V002), on ignore
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'readiness_scores' AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE readiness_scores
                ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.drop_table("insights")
    op.drop_table("daily_metrics")

"""V008 — Coach Platform + Biomarkers Lab : persistence PostgreSQL.

Revision: V008
Down-revision: V007

Crée :
  - coach_profiles          (profils coachs professionnels)
  - athlete_profiles        (profils athlètes liés à des users SOMA)
  - coach_athlete_links     (relation many-to-many coach ↔ athlète)
  - training_programs       (programmes d'entraînement, weeks JSONB)
  - athlete_notes           (notes coach sur athlète)
  - athlete_alerts          (alertes automatisées santé)
  - lab_results             (résultats biologiques utilisateur)

Remplace :
  - _coach_profiles, _athletes, _links, _programs, _notes (dicts in-memory)
  - _lab_store (dict in-memory dans biomarkers/endpoints.py)
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "V008"
down_revision: Union[str, None] = "V007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── coach_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "coach_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("specializations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("certification", sa.String(200), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("max_athletes", sa.Integer(), server_default="50", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_coach_profiles_user_id"),
    )
    op.create_index("ix_coach_profiles_user_id", "coach_profiles", ["user_id"])

    # ── athlete_profiles ──────────────────────────────────────────────────────
    op.create_table(
        "athlete_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("sport", sa.String(100), nullable=True),
        sa.Column("goal", sa.String(200), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_athlete_profiles_user_id"),
    )
    op.create_index("ix_athlete_profiles_user_id", "athlete_profiles", ["user_id"])

    # ── coach_athlete_links ───────────────────────────────────────────────────
    op.create_table(
        "coach_athlete_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("role", sa.String(50), server_default="primary", nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("coach_id", "athlete_id", name="uq_coach_athlete_link"),
    )
    op.create_index("ix_coach_athlete_links_coach_id", "coach_athlete_links", ["coach_id"])
    op.create_index("ix_coach_athlete_links_athlete_id", "coach_athlete_links", ["athlete_id"])
    op.create_index(
        "ix_coach_athlete_links_coach_athlete",
        "coach_athlete_links",
        ["coach_id", "athlete_id"],
    )

    # ── training_programs ─────────────────────────────────────────────────────
    op.create_table(
        "training_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), server_default="4", nullable=False),
        sa.Column("sport_focus", sa.String(100), nullable=True),
        sa.Column("difficulty", sa.String(50), nullable=True),
        sa.Column("weeks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_template", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_training_programs_coach_id", "training_programs", ["coach_id"])
    op.create_index("ix_training_programs_athlete_id", "training_programs", ["athlete_id"])

    # ── athlete_notes ─────────────────────────────────────────────────────────
    op.create_table(
        "athlete_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_date", sa.Date(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), server_default="general", nullable=False),
        sa.Column("is_private", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_athlete_notes_coach_athlete",
        "athlete_notes",
        ["coach_id", "athlete_id"],
    )

    # ── athlete_alerts ────────────────────────────────────────────────────────
    op.create_table(
        "athlete_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_athlete_alerts_coach_athlete",
        "athlete_alerts",
        ["coach_id", "athlete_id"],
    )
    op.create_index(
        "ix_athlete_alerts_coach_unack",
        "athlete_alerts",
        ["coach_id", "is_acknowledged"],
    )

    # ── lab_results ───────────────────────────────────────────────────────────
    op.create_table(
        "lab_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marker_name", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lab_results_user_id", "lab_results", ["user_id"])
    op.create_index("ix_lab_results_user_date", "lab_results", ["user_id", "test_date"])


def downgrade() -> None:
    op.drop_table("lab_results")
    op.drop_table("athlete_alerts")
    op.drop_table("athlete_notes")
    op.drop_table("training_programs")
    op.drop_table("coach_athlete_links")
    op.drop_table("athlete_profiles")
    op.drop_table("coach_profiles")

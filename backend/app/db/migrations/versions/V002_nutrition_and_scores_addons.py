"""V002 — Nutrition et scores : colonnes manquantes + index recherche

Revision ID: V002
Revises: V001
Create Date: 2026-03-07

Raison des changements :
  - NutritionEntry et NutritionPhoto manquaient du soft-delete (is_deleted),
    de l'audit trail (updated_at) et de quelques champs métier.
  - NutritionPhoto reçoit un FK optionnel vers nutrition_entries pour le
    pipeline photo → entrée.
  - ReadinessScore reçoit updated_at pour le suivi des recalculs.
  - Indexes trigram pour la recherche floue sur food_items (pg_trgm déjà
    activé en V001).

Production note : les CREATE INDEX CONCURRENTLY sont préférables en prod
pour éviter le lock. En dev/CI, les INDEX standards suffisent.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "V002"
down_revision: Union[str, None] = "V001"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # ── nutrition_entries : soft delete + audit + meal_name ─────────────────
    op.add_column("nutrition_entries", sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("nutrition_entries", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("nutrition_entries", sa.Column("meal_name", sa.String(200), nullable=True))

    # Index partiel pour requêtes filtrées par utilisateur + date (actives uniquement)
    op.create_index(
        "ix_nutrition_entries_user_date_active",
        "nutrition_entries",
        ["user_id", "logged_at"],
        postgresql_where=sa.text("is_deleted = FALSE"),
    )

    # ── nutrition_photos : soft delete + audit + FK entry + métadonnées fichier
    op.add_column("nutrition_photos", sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("nutrition_photos", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("nutrition_photos", sa.Column("entry_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("nutrition_photos", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("nutrition_photos", sa.Column("mime_type", sa.String(50), nullable=True))

    # FK optionnelle : photo peut exister avant ou après l'entrée
    op.create_foreign_key(
        "fk_nutrition_photos_entry_id",
        "nutrition_photos", "nutrition_entries",
        ["entry_id"], ["id"],
        ondelete="SET NULL",
    )

    # Index pour retrouver les photos d'une entrée
    op.create_index(
        "ix_nutrition_photos_entry_id",
        "nutrition_photos",
        ["entry_id"],
        postgresql_where=sa.text("is_deleted = FALSE"),
    )

    # ── readiness_scores : updated_at pour traçabilité des recalculs ──────────
    op.add_column(
        "readiness_scores",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── food_items : indexes trigram pour recherche floue ─────────────────────
    # pg_trgm activé en V001
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_food_items_name_trgm "
        "ON food_items USING gin(name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_food_items_name_fr_trgm "
        "ON food_items USING gin(name_fr gin_trgm_ops) "
        "WHERE name_fr IS NOT NULL"
    )
    op.create_index("ix_food_items_source", "food_items", ["source"])


def downgrade() -> None:
    # ── food_items : suppression indexes trigram ──────────────────────────────
    op.drop_index("ix_food_items_source", table_name="food_items")
    op.execute("DROP INDEX IF EXISTS ix_food_items_name_fr_trgm")
    op.execute("DROP INDEX IF EXISTS ix_food_items_name_trgm")

    # ── readiness_scores ──────────────────────────────────────────────────────
    op.drop_column("readiness_scores", "updated_at")

    # ── nutrition_photos ──────────────────────────────────────────────────────
    op.drop_index("ix_nutrition_photos_entry_id", table_name="nutrition_photos")
    op.drop_constraint("fk_nutrition_photos_entry_id", "nutrition_photos", type_="foreignkey")
    op.drop_column("nutrition_photos", "mime_type")
    op.drop_column("nutrition_photos", "file_size_bytes")
    op.drop_column("nutrition_photos", "entry_id")
    op.drop_column("nutrition_photos", "updated_at")
    op.drop_column("nutrition_photos", "is_deleted")

    # ── nutrition_entries ─────────────────────────────────────────────────────
    op.drop_index("ix_nutrition_entries_user_date_active", table_name="nutrition_entries")
    op.drop_column("nutrition_entries", "meal_name")
    op.drop_column("nutrition_entries", "updated_at")
    op.drop_column("nutrition_entries", "is_deleted")

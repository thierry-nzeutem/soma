"""
V004 — Algorithm version tracking on computed score tables (LOT 5)

Ajoute la colonne algorithm_version sur :
  - daily_metrics
  - readiness_scores
  - longevity_scores

Permet de tracer quelle version de l'algorithme a produit chaque snapshot,
facilitant les migrations de données lors des évolutions futures.

Depends on : V003
"""
from typing import Union
import sqlalchemy as sa
from alembic import op


revision: str = "V004"
down_revision: Union[str, None] = "V003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── daily_metrics ─────────────────────────────────────────────────────────
    op.add_column(
        "daily_metrics",
        sa.Column(
            "algorithm_version",
            sa.String(10),
            server_default="v1.0",
            nullable=False,
        ),
    )

    # ── readiness_scores ──────────────────────────────────────────────────────
    op.add_column(
        "readiness_scores",
        sa.Column(
            "algorithm_version",
            sa.String(10),
            server_default="v1.0",
            nullable=False,
        ),
    )

    # ── longevity_scores ──────────────────────────────────────────────────────
    op.add_column(
        "longevity_scores",
        sa.Column(
            "algorithm_version",
            sa.String(10),
            server_default="v1.0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("longevity_scores", "algorithm_version")
    op.drop_column("readiness_scores", "algorithm_version")
    op.drop_column("daily_metrics", "algorithm_version")

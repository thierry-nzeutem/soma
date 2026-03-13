"""
V005 — Vision sessions table (LOT 7 — Computer Vision V1)

Crée la table `vision_sessions` pour stocker les résumés de sessions
Computer Vision (rep count, durée, scores biomécaniques).

Pas de vidéo stockée — uniquement le JSON de résumé calculé côté mobile.

Depends on : V004
"""
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "V005"
down_revision: Union[str, None] = "V004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vision_sessions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Exercice effectué
        sa.Column("exercise_type", sa.String(50), nullable=False),
        # Métriques de session
        sa.Column("rep_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        # Scores biomécaniques [0-100]
        sa.Column("amplitude_score", sa.Float(), nullable=True),
        sa.Column("stability_score", sa.Float(), nullable=True),
        sa.Column("regularity_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        # Rattachement optionnel à une WorkoutSession
        sa.Column(
            "workout_session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workout_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Métadonnées libres (algorithme, version, device…)
        sa.Column(
            "metadata",
            JSONB(),
            nullable=False,
            server_default="{}",
        ),
        # Versioning algorithmique
        sa.Column(
            "algorithm_version",
            sa.String(10),
            nullable=False,
            server_default="v1.0",
        ),
        # Date de la session (pour agrégation journalière)
        sa.Column(
            "session_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index sur (user_id, session_date) pour requêtes historiques
    op.create_index(
        "ix_vision_sessions_user_date",
        "vision_sessions",
        ["user_id", "session_date"],
    )

    # Index sur workout_session_id pour jointures
    op.create_index(
        "ix_vision_sessions_workout_session",
        "vision_sessions",
        ["workout_session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_vision_sessions_workout_session")
    op.drop_index("ix_vision_sessions_user_date")
    op.drop_table("vision_sessions")

"""V006 — Coach IA : conversation threads + messages + métabolique twin étendu.

Revision: V006
Down-revision: V005

Crée :
  - conversation_threads
  - conversation_messages

Modifie :
  - metabolic_state_snapshots : ajoute protein_status, hydration_status,
    stress_load, plateau_risk, metabolic_age
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "V006"
down_revision: Union[str, None] = "V005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── conversation_threads ─────────────────────────────────────────────────
    op.create_table(
        "conversation_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_conversation_threads_user_id", "conversation_threads", ["user_id"])

    # ── conversation_messages ────────────────────────────────────────────────
    op.create_table(
        "conversation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("thread_id", UUID(as_uuid=True),
                  sa.ForeignKey("conversation_threads.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_conversation_messages_thread_id", "conversation_messages", ["thread_id"])

    # ── metabolic_state_snapshots : colonnes étendues ────────────────────────
    op.add_column(
        "metabolic_state_snapshots",
        sa.Column("protein_status", sa.String(20), nullable=True),
        # insufficient | adequate | optimal | excess
    )
    op.add_column(
        "metabolic_state_snapshots",
        sa.Column("hydration_status", sa.String(20), nullable=True),
        # dehydrated | low | normal | optimal
    )
    op.add_column(
        "metabolic_state_snapshots",
        sa.Column("stress_load", sa.Float, nullable=True),
        # 0-100 : charge de stress globale (entraînement + sommeil + nutrition)
    )
    op.add_column(
        "metabolic_state_snapshots",
        sa.Column("plateau_risk", sa.Boolean, nullable=True),
        # True si plateau détecté sur 14 jours
    )
    op.add_column(
        "metabolic_state_snapshots",
        sa.Column("metabolic_age", sa.Float, nullable=True),
        # Estimation âge métabolique (années)
    )


def downgrade() -> None:
    # Supprimer les colonnes ajoutées à metabolic_state_snapshots
    for col in ("metabolic_age", "plateau_risk", "stress_load",
                "hydration_status", "protein_status"):
        op.drop_column("metabolic_state_snapshots", col)

    # Supprimer les tables coach
    op.drop_index("ix_conversation_messages_thread_id", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversation_threads_user_id", table_name="conversation_threads")
    op.drop_table("conversation_threads")

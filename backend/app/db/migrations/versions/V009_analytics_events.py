"""V009 — Analytics Events table.

Revision: V009
Down-revision: V008

Crée :
  - analytics_events  (événements produit utilisateur pour analytics)

Colonnes :
  - id            UUID PK
  - user_id       UUID (indexed)
  - event_name    VARCHAR(100) (indexed)
  - properties    JSONB nullable
  - created_at    TIMESTAMP WITH TIME ZONE (indexed)

Index composites :
  - (user_id, created_at)  — requêtes par utilisateur + fenêtre temporelle
"""
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "V009"
down_revision: Union[str, None] = "V008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_name", sa.String(100), nullable=False),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Index simples
    op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_events_event_name", "analytics_events", ["event_name"])
    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])

    # Index composite — requêtes user + période
    op.create_index(
        "ix_analytics_events_user_created",
        "analytics_events",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_analytics_events_user_created", table_name="analytics_events")
    op.drop_index("ix_analytics_events_created_at", table_name="analytics_events")
    op.drop_index("ix_analytics_events_event_name", table_name="analytics_events")
    op.drop_index("ix_analytics_events_user_id", table_name="analytics_events")
    op.drop_table("analytics_events")

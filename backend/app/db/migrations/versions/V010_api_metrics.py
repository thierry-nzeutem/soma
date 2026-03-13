"""V010 — API Metrics table.

Revision: V010
Down-revision: V009

Crée :
  - api_metrics  (métriques de performance des endpoints API)

Colonnes :
  - id                 UUID PK
  - endpoint           VARCHAR(200) — path de l'endpoint (ex: /api/v1/daily/briefing)
  - method             VARCHAR(10)  — méthode HTTP (GET, POST, PATCH…)
  - response_time_ms   INTEGER      — temps de réponse en millisecondes
  - status_code        INTEGER      — code HTTP retourné (200, 404, 500…)
  - created_at         TIMESTAMP WITH TIME ZONE

Indexes :
  - ix_api_metrics_endpoint       — filtrer par endpoint
  - ix_api_metrics_status_code    — identifier les erreurs
  - ix_api_metrics_created_at     — requêtes par fenêtre temporelle
  - ix_api_metrics_endpoint_time  — composite (endpoint, created_at)
"""
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "V010"
down_revision: Union[str, None] = "V009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("endpoint", sa.String(200), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("response_time_ms", sa.Integer, nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_api_metrics_endpoint", "api_metrics", ["endpoint"])
    op.create_index("ix_api_metrics_status_code", "api_metrics", ["status_code"])
    op.create_index("ix_api_metrics_created_at", "api_metrics", ["created_at"])
    op.create_index(
        "ix_api_metrics_endpoint_time",
        "api_metrics",
        ["endpoint", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_api_metrics_endpoint_time", table_name="api_metrics")
    op.drop_index("ix_api_metrics_created_at", table_name="api_metrics")
    op.drop_index("ix_api_metrics_status_code", table_name="api_metrics")
    op.drop_index("ix_api_metrics_endpoint", table_name="api_metrics")
    op.drop_table("api_metrics")

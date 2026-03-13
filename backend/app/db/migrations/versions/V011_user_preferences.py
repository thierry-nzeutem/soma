"""V011 — User Preferences columns.

Revision: V011
Down-revision: V010

Ajoute 3 colonnes de preferences a user_profiles :
  - theme_preference   VARCHAR(10) DEFAULT 'system'  — 'light', 'dark', 'system'
  - locale             VARCHAR(10) DEFAULT 'fr'      — 'fr', 'en', extensible
  - timezone           VARCHAR(50) DEFAULT 'Europe/Paris' — IANA timezone
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "V011"
down_revision: Union[str, None] = "V010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "theme_preference",
            sa.String(10),
            server_default="system",
            nullable=False,
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "locale",
            sa.String(10),
            server_default="fr",
            nullable=False,
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "timezone",
            sa.String(50),
            server_default="Europe/Paris",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "timezone")
    op.drop_column("user_profiles", "locale")
    op.drop_column("user_profiles", "theme_preference")

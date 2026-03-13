"""V012 — Body composition enriched fields.

Revision: V012
Down-revision: V011

Ajoute des champs de composition corporelle enrichis à body_metrics :
  - bone_mass_kg          FLOAT
  - visceral_fat_index    FLOAT
  - water_pct             FLOAT
  - metabolic_age         INTEGER
  - trunk_fat_pct         FLOAT
  - trunk_muscle_pct      FLOAT
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "V012"
down_revision: Union[str, None] = "V011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("body_metrics", sa.Column("bone_mass_kg", sa.Float(), nullable=True))
    op.add_column("body_metrics", sa.Column("visceral_fat_index", sa.Float(), nullable=True))
    op.add_column("body_metrics", sa.Column("water_pct", sa.Float(), nullable=True))
    op.add_column("body_metrics", sa.Column("metabolic_age", sa.Integer(), nullable=True))
    op.add_column("body_metrics", sa.Column("trunk_fat_pct", sa.Float(), nullable=True))
    op.add_column("body_metrics", sa.Column("trunk_muscle_pct", sa.Float(), nullable=True))


def downgrade() -> None:
    for col in ["trunk_muscle_pct", "trunk_fat_pct", "metabolic_age", "water_pct", "visceral_fat_index", "bone_mass_kg"]:
        op.drop_column("body_metrics", col)

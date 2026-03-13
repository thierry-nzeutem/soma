"""V013 — HRV score cache, cycle tracking, streak records.

Revision: V013
Down-revision: V012
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "V013"
down_revision: Union[str, None] = "V012"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Menstrual cycle entries
    op.create_table(
        "menstrual_cycle_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("cycle_start_date", sa.Date(), nullable=False),
        sa.Column("cycle_length_days", sa.Integer(), nullable=True),  # estimated from history
        sa.Column("period_duration_days", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),  # JSON string
        sa.Column("flow_intensity", sa.String(20), nullable=True),  # light/medium/heavy
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    op.create_index("ix_cycle_user_start", "menstrual_cycle_entries", ["user_id", "cycle_start_date"])

def downgrade() -> None:
    op.drop_index("ix_cycle_user_start")
    op.drop_table("menstrual_cycle_entries")

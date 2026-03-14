"""V017 - Coach Module Phase 1.

Adds coach role support, invitation system, recommendations, and extends coach-athlete links.

Revision: V017
Down-revision: V016
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "V017"
down_revision: Union[str, None] = "V016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add is_coach flag to users
    op.add_column(
        "users",
        sa.Column("is_coach", sa.Boolean(), nullable=False, server_default="false"),
    )

    # 2. Extend coach_athlete_links with status and notes
    op.add_column(
        "coach_athlete_links",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
    )
    # status: invited | active | paused | archived | revoked
    op.add_column(
        "coach_athlete_links",
        sa.Column("relationship_notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_coach_athlete_links_status",
        "coach_athlete_links",
        ["coach_id", "status"],
    )

    # 3. Create coach_invitations table
    op.create_table(
        "coach_invitations",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "coach_profile_id",
            UUID(as_uuid=True),
            sa.ForeignKey("coach_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("invite_code", sa.String(12), nullable=False, unique=True),
        sa.Column("invite_token", sa.String(64), nullable=False, unique=True),
        sa.Column("invitee_email", sa.String(255), nullable=True),
        sa.Column("invitee_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        # status: pending | accepted | expired | cancelled
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_coach_invitations_token",
        "coach_invitations",
        ["invite_token"],
    )
    op.create_index(
        "ix_coach_invitations_code",
        "coach_invitations",
        ["invite_code"],
    )

    # 4. Create coach_recommendations table
    op.create_table(
        "coach_recommendations",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "coach_id",
            UUID(as_uuid=True),
            sa.ForeignKey("coach_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "athlete_id",
            UUID(as_uuid=True),
            sa.ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "rec_type",
            sa.String(50),
            nullable=False,
            server_default="general",
        ),
        # rec_type: training | nutrition | recovery | medical | lifestyle | mental | general
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default="normal",
        ),
        # priority: low | normal | high | urgent
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        # status: pending | in_progress | completed | dismissed
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_coach_rec_coach_athlete",
        "coach_recommendations",
        ["coach_id", "athlete_id"],
    )
    op.create_index(
        "ix_coach_rec_status",
        "coach_recommendations",
        ["athlete_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("coach_recommendations")
    op.drop_table("coach_invitations")
    op.drop_index("ix_coach_athlete_links_status", table_name="coach_athlete_links")
    op.drop_column("coach_athlete_links", "relationship_notes")
    op.drop_column("coach_athlete_links", "status")
    op.drop_column("users", "is_coach")

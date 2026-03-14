"""V016 - Apple In-App Purchase billing support.

Adds Apple-specific fields to users and creates idempotency/audit tables
for Apple App Store Server Notifications v2 and StoreKit 2 transactions.

Revision: V016
Down-revision: V015
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "V016"
down_revision: Union[str, None] = "V015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Apple-specific subscription fields on users
    op.add_column(
        "users",
        sa.Column("apple_original_transaction_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("apple_subscription_group_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_users_apple_original_transaction_id",
        "users",
        ["apple_original_transaction_id"],
        unique=True,
    )

    # Apple App Store notification idempotency (mirrors stripe_webhook_events)
    op.create_table(
        "apple_notification_events",
        sa.Column("notification_uuid", sa.String(255), primary_key=True),
        sa.Column("notification_type", sa.String(100), nullable=False),
        sa.Column("subtype", sa.String(100), nullable=True),
        sa.Column("product_id", sa.String(255), nullable=True),
        sa.Column("original_transaction_id", sa.String(255), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Apple transaction audit log
    op.create_table(
        "apple_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("transaction_id", sa.String(255), nullable=False, unique=True),
        sa.Column("original_transaction_id", sa.String(255), nullable=False, index=True),
        sa.Column("product_id", sa.String(255), nullable=False),
        sa.Column("plan_code", sa.String(20), nullable=False),
        sa.Column("environment", sa.String(20), nullable=False),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_apple_tx_original", "apple_transactions", ["original_transaction_id"])
    op.create_index("ix_apple_tx_user_product", "apple_transactions", ["user_id", "product_id"])


def downgrade() -> None:
    op.drop_table("apple_transactions")
    op.drop_table("apple_notification_events")
    op.drop_index("ix_users_apple_original_transaction_id", table_name="users")
    op.drop_column("users", "apple_subscription_group_id")
    op.drop_column("users", "apple_original_transaction_id")

"""V015 - Webhook idempotency, feature usage events, app settings, is_superuser.

Revision: V015
Down-revision: V014
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "V015"
down_revision: Union[str, None] = "V014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # is_superuser on users
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"))

    # Stripe webhook idempotency
    op.create_table(
        "stripe_webhook_events",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Feature usage analytics
    op.create_table(
        "feature_usage_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("feature_code", sa.String(100), nullable=True),
        sa.Column("plan_code", sa.String(20), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_feature_usage_user", "feature_usage_events", ["user_id"])
    op.create_index("ix_feature_usage_type", "feature_usage_events", ["event_type"])
    op.create_index("ix_feature_usage_occurred", "feature_usage_events", ["occurred_at"])

    # App settings (replaces env vars for runtime-configurable values)
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    # Seed default app settings
    settings = [
        ("free_plan_daily_ai_limit", "10", "Max AI requests per day for free plan", "ai"),
        ("free_plan_max_prompt_chars", "1200", "Max prompt length in chars for free plan", "ai"),
        ("free_plan_ai_timeout_seconds", "15", "Timeout in seconds for free plan AI calls", "ai"),
        ("ai_plan_daily_ai_limit", "100", "Max AI requests per day for AI plan", "ai"),
        ("performance_plan_daily_ai_limit", "500", "Max AI requests per day for performance plan", "ai"),
        ("stripe_price_ai_monthly", "", "Stripe Price ID for AI plan monthly", "billing"),
        ("stripe_price_ai_yearly", "", "Stripe Price ID for AI plan yearly", "billing"),
        ("stripe_price_perf_monthly", "", "Stripe Price ID for Performance plan monthly", "billing"),
        ("stripe_price_perf_yearly", "", "Stripe Price ID for Performance plan yearly", "billing"),
        ("trial_ai_days", "7", "Trial duration in days for AI plan", "billing"),
        ("trial_performance_days", "3", "Trial duration in days for Performance plan", "billing"),
        ("ollama_model", "llama3.2:3b", "Ollama model for free plan local AI", "ai"),
        ("claude_standard_model", "claude-3-5-haiku-20241022", "Claude model for AI plan", "ai"),
        ("claude_advanced_model", "claude-3-5-sonnet-20241022", "Claude model for Performance plan", "ai"),
    ]
    for key, value, description, category in settings:
        op.execute(
            f"INSERT INTO app_settings (key, value, description, category) "
            f"VALUES ('{key}', '{value}', '{description}', '{category}')"
        )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_index("ix_feature_usage_occurred")
    op.drop_index("ix_feature_usage_type")
    op.drop_index("ix_feature_usage_user")
    op.drop_table("feature_usage_events")
    op.drop_table("stripe_webhook_events")
    op.drop_column("users", "is_superuser")

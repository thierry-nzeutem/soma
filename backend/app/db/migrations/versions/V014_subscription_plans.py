"""V014 — Subscription plans and feature entitlements.

Revision: V014
Down-revision: V013
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "V014"
down_revision: Union[str, None] = "V013"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add plan columns to users table
    op.add_column("users", sa.Column("plan_code", sa.String(20), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("plan_status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("users", sa.Column("billing_provider", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("plan_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_plan_code", "users", ["plan_code"])
    op.create_index("ix_users_stripe_customer", "users", ["stripe_customer_id"])

    # Plans reference table
    op.create_table(
        "plans",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # Plan <-> feature mapping
    op.create_table(
        "plan_features",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_code", sa.String(20), sa.ForeignKey("plans.code", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(100), nullable=False),
    )
    op.create_index("ix_plan_features_plan", "plan_features", ["plan_code"])

    # Per-user feature overrides (promo, beta, support)
    op.create_table(
        "feature_entitlements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source", sa.String(30), nullable=False, server_default="plan"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_entitlements_user", "feature_entitlements", ["user_id"])

    # Seed plans
    op.execute("INSERT INTO plans (code, name, rank) VALUES ('free', 'SOMA Free', 1)")
    op.execute("INSERT INTO plans (code, name, rank) VALUES ('ai', 'SOMA AI', 2)")
    op.execute("INSERT INTO plans (code, name, rank) VALUES ('performance', 'SOMA Performance', 3)")

    # Seed plan features - free
    free_features = ["basic_dashboard", "basic_health_metrics", "local_ai_tips"]
    for f in free_features:
        op.execute(f"INSERT INTO plan_features (plan_code, feature_code) VALUES ('free', '{f}')")

    # Seed plan features - ai (includes free features)
    ai_features = free_features + ["ai_coach", "daily_briefing", "advanced_insights", "pdf_reports", "anomaly_detection", "biological_age"]
    for f in ai_features:
        op.execute(f"INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', '{f}')")

    # Seed plan features - performance (includes ai features)
    perf_features = ai_features + ["readiness_score", "injury_prediction", "biomechanics_vision", "advanced_vo2max", "training_load"]
    for f in perf_features:
        op.execute(f"INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', '{f}')")

def downgrade() -> None:
    op.drop_table("feature_entitlements")
    op.drop_table("plan_features")
    op.drop_table("plans")
    op.drop_index("ix_users_stripe_customer")
    op.drop_index("ix_users_plan_code")
    for col in ["trial_ends_at", "plan_expires_at", "plan_started_at", "stripe_subscription_id", "stripe_customer_id", "billing_provider", "plan_status", "plan_code"]:
        op.drop_column("users", col)

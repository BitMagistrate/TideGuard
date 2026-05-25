"""v0.5 — Block 1 & 2 (cross-cutting): billing core, organizations, api keys.

Revision ID: 004
Revises: 003
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("billing_email", sa.Text()),
        sa.Column("billing_provider", sa.String(16), nullable=False, server_default="stripe"),
        sa.Column("billing_customer_id", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "org_members",
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="member"),
        sa.Column("invited_at", sa.DateTime(timezone=True)),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tiers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("category", sa.String(16), nullable=False, server_default="api"),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("price_monthly_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_yearly_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("features", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("stripe_price_id_monthly", sa.Text()),
        sa.Column("stripe_price_id_yearly", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tier_id", sa.Uuid(), sa.ForeignKey("tiers.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("provider", sa.String(16), nullable=False, server_default="stripe"),
        sa.Column("provider_subscription_id", sa.Text()),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("trial_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_org", "subscriptions", ["org_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False, server_default="tg_live"),
        sa.Column("hash", sa.String(128), nullable=False, unique=True),
        sa.Column("last4", sa.String(8), nullable=False),
        sa.Column("scopes", sa.JSON()),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_ip", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "billing_events",
        sa.Column("provider", sa.String(16), primary_key=True),
        sa.Column("provider_event_id", sa.Text(), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "usage_aggregates_daily",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("api_key_id", sa.Uuid(), sa.ForeignKey("api_keys.id")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id")),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bytes_out", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_usage_daily_unique", "usage_aggregates_daily",
        ["api_key_id", "endpoint", "day"], unique=True,
    )
    op.create_index("ix_usage_daily_org_day", "usage_aggregates_daily", ["org_id", "day"])


def downgrade() -> None:
    op.drop_index("ix_usage_daily_org_day", table_name="usage_aggregates_daily")
    op.drop_index("ix_usage_daily_unique", table_name="usage_aggregates_daily")
    op.drop_table("usage_aggregates_daily")
    op.drop_table("billing_events")
    op.drop_table("api_keys")
    op.drop_index("ix_subscriptions_org", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_table("tiers")
    op.drop_table("org_members")
    op.drop_table("organizations")

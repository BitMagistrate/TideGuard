"""v0.5 — Block 2: regions + B2G alerts.

Revision ID: 005
Revises: 004
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name_ru", sa.Text(), nullable=False),
        sa.Column("display_name_en", sa.Text(), nullable=False),
        sa.Column("country", sa.String(8), nullable=False),
        sa.Column("bbox", sa.JSON(), nullable=False),
        sa.Column("beach_length_km", sa.Float(), nullable=False, server_default="0"),
        sa.Column("geom_wkt", sa.Text()),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "b2g_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("region_id", sa.Uuid(), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("rule_type", sa.Text(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("channels", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("recipients", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True)),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="360"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "b2g_alert_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("b2g_alerts.id"), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("channels_sent", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("delivery_status", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_table("b2g_alert_events")
    op.drop_table("b2g_alerts")
    op.drop_table("regions")

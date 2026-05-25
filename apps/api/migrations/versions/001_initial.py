"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision: str | None = None
branch_labels = None
depends_on = None

UUID = sa.Uuid


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "schools",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country", sa.String(8)),
        sa.Column("geom_wkt", sa.Text),
    )

    op.create_table(
        "users",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("name", sa.Text),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("school_id", UUID(), sa.ForeignKey("schools.id"), nullable=True),
        sa.Column("country", sa.String(8)),
        sa.Column("xp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lng", sa.Float, nullable=False),
        sa.Column("photo_url", sa.Text, nullable=False),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("debris_type", sa.String(64)),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_reports_user", "reports", ["user_id"])
    op.create_index("idx_reports_status", "reports", ["status"])

    op.create_table(
        "cleanups",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("geom_wkt", sa.Text, nullable=False),
        sa.Column("kg_collected", sa.Float, nullable=False),
        sa.Column("participants", sa.Integer, nullable=False),
        sa.Column("before_photo", sa.Text),
        sa.Column("after_photo", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lessons",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("content_md", sa.Text, nullable=False),
        sa.Column("quiz_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default="50"),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "lesson_progress",
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("lesson_id", UUID(), sa.ForeignKey("lessons.id"), primary_key=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("score", sa.Float),
    )

    op.create_table(
        "badges",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("criteria_json", sa.JSON, nullable=False, server_default="{}"),
    )

    op.create_table(
        "user_badges",
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("badge_id", UUID(), sa.ForeignKey("badges.id"), primary_key=True),
        sa.Column("awarded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "forecasts",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("model_version", sa.Text, nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bbox_wkt", sa.Text, nullable=False),
        sa.Column("tile_set_url", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for t in [
        "forecasts",
        "user_badges",
        "badges",
        "lesson_progress",
        "lessons",
        "cleanups",
        "reports",
        "users",
        "schools",
    ]:
        op.drop_table(t)

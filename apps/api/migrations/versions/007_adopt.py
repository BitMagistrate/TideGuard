"""v0.5 — Block 4: Adopt-a-Beach (segments + adoptions).

Revision ID: 007
Revises: 006
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "beach_segments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("region_id", sa.Uuid(), sa.ForeignKey("regions.id")),
        sa.Column("geom_wkt", sa.Text(), nullable=False),
        sa.Column("length_m", sa.Float(), nullable=False, server_default="1000"),
        sa.Column("midpoint_lat", sa.Float(), nullable=False),
        sa.Column("midpoint_lng", sa.Float(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_beach_segments_status", "beach_segments", ["status"])
    op.create_index("ix_beach_segments_region", "beach_segments", ["region_id"])

    op.create_table(
        "adoptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("segment_id", sa.Uuid(), sa.ForeignKey("beach_segments.id"), nullable=False),
        sa.Column("adopter_user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("adopter_org_id", sa.Uuid(), sa.ForeignKey("organizations.id")),
        sa.Column("tier", sa.String(32), nullable=False, server_default="adopt_individual"),
        sa.Column("starts_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("display_name", sa.Text()),
        sa.Column("show_publicly", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("subscription_id", sa.Uuid(), sa.ForeignKey("subscriptions.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_adoptions_segment", "adoptions", ["segment_id"])
    op.create_index("ix_adoptions_user", "adoptions", ["adopter_user_id"])
    op.create_index("ix_adoptions_status", "adoptions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_adoptions_status", table_name="adoptions")
    op.drop_index("ix_adoptions_user", table_name="adoptions")
    op.drop_index("ix_adoptions_segment", table_name="adoptions")
    op.drop_table("adoptions")
    op.drop_index("ix_beach_segments_region", table_name="beach_segments")
    op.drop_index("ix_beach_segments_status", table_name="beach_segments")
    op.drop_table("beach_segments")

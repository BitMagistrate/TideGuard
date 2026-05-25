"""v0.5 — Block 3: ESG risk grid + sponsors.

Revision ID: 006
Revises: 005
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esg_risk_grid",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("cell_size_deg", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("tier", sa.Text(), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence_95ci_low", sa.Integer(), nullable=False),
        sa.Column("confidence_95ci_high", sa.Integer(), nullable=False),
        sa.Column("methodology_version", sa.Text(), nullable=False, server_default="esg-v1.0"),
        sa.Column("model_version", sa.Text(), nullable=False, server_default="pinn-0.4.0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_esg_risk_cell",
        "esg_risk_grid",
        ["lat", "lng", "cell_size_deg", "methodology_version"],
        unique=True,
    )

    op.create_table(
        "sponsors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("logo_url", sa.Text()),
        sa.Column("website", sa.Text()),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id")),
        sa.Column("active_from", sa.DateTime(timezone=True)),
        sa.Column("active_until", sa.DateTime(timezone=True)),
        sa.Column("tier", sa.String(16), nullable=False, server_default="bronze"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sponsors")
    op.drop_index("ix_esg_risk_cell", table_name="esg_risk_grid")
    op.drop_table("esg_risk_grid")

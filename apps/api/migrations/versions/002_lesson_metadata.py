"""Lesson metadata: lang / grade_band / sdgs / practical_task.

Revision ID: 002
Revises: 001
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("lang", sa.Text, server_default="en", nullable=False))
    op.add_column("lessons", sa.Column("grade_band", sa.Text, nullable=True))
    op.add_column("lessons", sa.Column("sdgs", sa.JSON, server_default="{}", nullable=False))
    op.add_column("lessons", sa.Column("practical_task_md", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "practical_task_md")
    op.drop_column("lessons", "sdgs")
    op.drop_column("lessons", "grade_band")
    op.drop_column("lessons", "lang")

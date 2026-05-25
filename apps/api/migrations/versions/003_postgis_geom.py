"""Add PostGIS Geometry columns + GIST indices to reports and cleanups.

Revision ID: 003
Revises: 002
Create Date: 2026-05-22

For PostgreSQL we enable PostGIS, attach ``Geometry(Point, 4326)`` to
``reports.geom`` and ``Geometry(Polygon, 4326)`` to ``cleanups.geom``, and
backfill from the existing lat/lng / WKT columns. A GIST index is created on
each new column.

For SQLite (dev/test) we skip the PostGIS migration entirely — the lat/lng
columns are already there and queries fall back to bounding-box checks.
This keeps the test suite green without any extra config.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _is_postgres(bind: sa.engine.Connection) -> bool:
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    bind = op.get_bind()
    if not _is_postgres(bind):
        # SQLite / others: no-op. PostGIS lives only in production.
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute(
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)"
    )
    op.execute(
        "UPDATE reports SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326) WHERE geom IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_geom ON reports USING GIST(geom)"
    )

    op.execute(
        "ALTER TABLE cleanups ADD COLUMN IF NOT EXISTS geom geometry(Polygon, 4326)"
    )
    op.execute(
        "UPDATE cleanups SET geom = ST_SetSRID(ST_GeomFromText(geom_wkt), 4326) "
        "WHERE geom IS NULL AND geom_wkt IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cleanups_geom ON cleanups USING GIST(geom)"
    )

    # Lightweight covering index for the frequent (status, created_at) report
    # listing path used by the moderator queue and /reports endpoint.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_status_created "
        "ON reports (status, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cleanups_created ON cleanups (created_at DESC)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not _is_postgres(bind):
        return
    op.execute("DROP INDEX IF EXISTS idx_cleanups_created")
    op.execute("DROP INDEX IF EXISTS idx_reports_status_created")
    op.execute("DROP INDEX IF EXISTS idx_cleanups_geom")
    op.execute("ALTER TABLE cleanups DROP COLUMN IF EXISTS geom")
    op.execute("DROP INDEX IF EXISTS idx_reports_geom")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS geom")

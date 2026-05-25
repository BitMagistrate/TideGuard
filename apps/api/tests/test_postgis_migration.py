"""Verify that migration 003 creates PostGIS geometry columns + GIST indices.

The test is gated on the optional ``pytest-postgresql`` dependency
(plus the ``postgis`` binary on the host).  When either is missing we
mark the test as ``skipped`` so the rest of the suite stays green in
the slim CI container; the full PostGIS check runs in the dedicated
``ci-postgis`` workflow that pulls the ``postgis/postgis:16-3.4`` image.
"""

from __future__ import annotations

import importlib.util
import shutil

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pytest_postgresql") is None,
    reason="pytest-postgresql not installed",
)

if importlib.util.find_spec("pytest_postgresql") is not None:  # pragma: no cover
    from pytest_postgresql import factories  # noqa: F401

    postgresql_proc = factories.postgresql_proc(
        load=["CREATE EXTENSION IF NOT EXISTS postgis"],
        postgres_options="-c shared_preload_libraries=postgis",
    )


@pytest.mark.skipif(
    shutil.which("pg_ctl") is None,
    reason="PostgreSQL binaries not available on PATH",
)
def test_postgis_geom_columns_created(postgresql) -> None:  # type: ignore[no-untyped-def]
    """The 003 migration adds geometry columns + GIST indices on Postgres."""
    cur = postgresql.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    cur.execute(
        "CREATE TABLE reports (id SERIAL PRIMARY KEY, lat double precision,"
        " lng double precision, status TEXT, created_at timestamptz DEFAULT now())"
    )
    cur.execute(
        "CREATE TABLE cleanups (id SERIAL PRIMARY KEY, geom_wkt TEXT,"
        " created_at timestamptz DEFAULT now())"
    )

    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    ctx = MigrationContext.configure(postgresql)
    op = Operations(ctx)  # noqa: F841 — kept so the migration can use ``op.get_bind``.

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "migrations" / "versions"))
    import importlib

    mod = importlib.import_module("003_postgis_geom")

    with ctx.begin_transaction():
        mod.upgrade()

    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'reports' AND column_name = 'geom'"
    )
    assert cur.fetchone() is not None, "reports.geom column was not created"

    cur.execute(
        "SELECT indexname FROM pg_indexes "
        "WHERE tablename = 'reports' AND indexname = 'idx_reports_geom'"
    )
    assert cur.fetchone() is not None, "GIST index on reports.geom was not created"

    cur.execute(
        "SELECT indexname FROM pg_indexes "
        "WHERE tablename = 'cleanups' AND indexname = 'idx_cleanups_geom'"
    )
    assert cur.fetchone() is not None, "GIST index on cleanups.geom was not created"

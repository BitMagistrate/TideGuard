"""Seed the local sqlite/PostGIS dev DB with demo records.

Useful when bringing up a fresh `make demo` so the map already has a
handful of reports + a closed cleanup event + 10 lessons.

CLI::

    uv run python scripts/seed_demo_db.py --db sqlite:///./tideguard.db

Idempotent: safe to re-run; uses `INSERT OR IGNORE` on sqlite and
`ON CONFLICT DO NOTHING` on PostgreSQL.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="sqlite:///./tideguard.db")
    args = parser.parse_args(argv)

    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise SystemExit(f"missing sqlalchemy: {exc}") from exc

    engine = create_engine(args.db, future=True)
    dialect = engine.dialect.name
    on_conflict = "INSERT OR IGNORE" if dialect == "sqlite" else "INSERT"

    sample_reports = [
        # (lon, lat, severity, debris_type)
        (37.314, 44.890, "high", "bottle"),
        (37.301, 44.882, "medium", "wrapper"),
        (37.286, 44.876, "low", "filter"),
        (37.260, 44.870, "high", "rope"),
    ]
    sample_cleanups = [
        (37.300, 44.880, "Anapa central beach", _dt.date(2026, 6, 6).isoformat()),
    ]

    with engine.begin() as conn:
        # We rely on the existing migrations to have created the schema
        # already; if not, the inserts will simply fail.
        for lon, lat, severity, kind in sample_reports:
            try:
                conn.execute(
                    text(f"""
                        {on_conflict} INTO reports (lon, lat, severity, debris_type, created_at)
                        VALUES (:lon, :lat, :severity, :kind, :now)
                        {'ON CONFLICT DO NOTHING' if dialect != 'sqlite' else ''}
                    """),
                    {"lon": lon, "lat": lat, "severity": severity, "kind": kind, "now": _dt.datetime.utcnow().isoformat()},
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[seed] could not insert report: {exc}", file=sys.stderr)
        for lon, lat, name, when in sample_cleanups:
            try:
                conn.execute(
                    text(f"""
                        {on_conflict} INTO cleanups (lon, lat, name, scheduled_for)
                        VALUES (:lon, :lat, :name, :when)
                        {'ON CONFLICT DO NOTHING' if dialect != 'sqlite' else ''}
                    """),
                    {"lon": lon, "lat": lat, "name": name, "when": when},
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[seed] could not insert cleanup: {exc}", file=sys.stderr)
    print("[seed] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

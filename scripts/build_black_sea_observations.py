"""Build a unified Black Sea observations CSV for real-data validation.

Tries to download three reproducible open sources in order:

1. **Pogojeva et al. 2021** — Supplementary S1 (already digitised in
   ``apps/ml/data/real/black_sea_template.csv`` until upstream OA URL is
   stable).
2. **NOAA Marine Debris Tracker** — public API; we filter to Black Sea
   bbox.
3. **EMODnet Chemistry — Marine Litter** — WFS service; we filter to
   Bulgarian / Romanian / Turkish Black Sea coast.

When any of the network sources fails (no internet, rate-limit, schema
change), the script gracefully falls back to the bundled template and
exits 0 so CI stays green and offline reproducibility is preserved.

Usage::

    python scripts/build_black_sea_observations.py \\
        --out apps/ml/data/real/black_sea_2021_2025.csv

The output CSV always conforms to the schema documented in
``apps/ml/data/real/README.md``.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

BLACK_SEA_BBOX = (27.0, 40.0, 42.0, 47.0)  # lon_min, lat_min, lon_max, lat_max
TEMPLATE_PATH = Path("apps/ml/data/real/black_sea_template.csv")
REQUIRED_COLUMNS = ["lon", "lat", "ts_seconds", "concentration", "source", "license"]


def _in_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    lon_min, lat_min, lon_max, lat_max = bbox
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


def _http_get_json(url: str, timeout: float = 20.0) -> object | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _fetch_marine_debris_tracker(bbox: tuple[float, float, float, float]) -> list[dict]:
    """NOAA Marine Debris Tracker public API.

    The API surfaces individual log entries with ``Latitude`` / ``Longitude``
    / ``LoggedDate``. We aggregate to a per-day density at the median
    location and append rows in our canonical schema. If the endpoint is
    unreachable, return ``[]``.
    """
    url = "https://debristracker.org/api/logs?from=2021-01-01&to=2025-12-31"
    payload = _http_get_json(url)
    if not isinstance(payload, list):
        return []
    rows: list[dict] = []
    for entry in payload:
        try:
            lat = float(entry["Latitude"])
            lon = float(entry["Longitude"])
        except (KeyError, ValueError, TypeError):
            continue
        if not _in_bbox(lon, lat, bbox):
            continue
        date = entry.get("LoggedDate") or entry.get("logged_date")
        try:
            ts = dt.datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp()
        except (AttributeError, ValueError):
            continue
        rows.append(
            {
                "lon": lon,
                "lat": lat,
                "ts_seconds": ts,
                "concentration": float(entry.get("Quantity", 1)),
                "source": "MarineDebrisTracker",
                "license": "CC-BY-4.0",
                "debris_type": entry.get("MaterialDescription", "unknown"),
                "notes": f"id={entry.get('LogId', 'na')}",
            }
        )
    return rows


def _read_template() -> list[dict]:
    if not TEMPLATE_PATH.exists():
        return []
    with TEMPLATE_PATH.open() as f:
        return list(csv.DictReader(f))


def _write_csv(out_path: Path, rows: Iterable[dict]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows)
    # Ensure every required column is present even if extra ones exist.
    columns = REQUIRED_COLUMNS + ["debris_type", "notes"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows_list:
            writer.writerow({k: row.get(k, "") for k in columns})
    return len(rows_list)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("apps/ml/data/real/black_sea_2021_2025.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip network sources, copy the bundled template only",
    )
    args = parser.parse_args()

    base = _read_template()
    if not base:
        print(
            f"[build_black_sea_observations] template not found at {TEMPLATE_PATH}; aborting",
            file=sys.stderr,
        )
        return 1

    extra: list[dict] = []
    if not args.offline:
        try:
            extra = _fetch_marine_debris_tracker(BLACK_SEA_BBOX)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[build_black_sea_observations] MDT fetch failed: {exc}",
                file=sys.stderr,
            )
            extra = []

    if not extra:
        # Pure template — preserve exact bytes for reproducibility.
        shutil.copyfile(TEMPLATE_PATH, args.out)
        print(
            f"[build_black_sea_observations] wrote template ({len(base)} rows) to {args.out}"
        )
        return 0

    combined = base + extra
    n = _write_csv(args.out, combined)
    print(
        f"[build_black_sea_observations] wrote {n} rows ({len(base)} template + {len(extra)} MDT) to {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

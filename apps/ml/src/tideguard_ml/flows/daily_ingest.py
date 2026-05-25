"""Daily data ingestion flow (Prefect-ready, can also run as plain Python).

Orchestrates: CMEMS currents -> ERA5 wind -> Open-Meteo waves -> Zarr store.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def daily_ingest_taiwan_strait() -> None:
    """Daily ingestion job for Taiwan Strait pilot region."""
    today = datetime.utcnow().date()
    start = (today - timedelta(days=2)).isoformat()
    end = today.isoformat()
    bbox = (119.0, 23.0, 123.0, 26.0)

    print(f"[daily_ingest] {start} -> {end}, bbox={bbox}")
    print("[daily_ingest] step 1/3: CMEMS currents (stub - requires credentials)")
    print("[daily_ingest] step 2/3: ERA5 wind (stub - requires credentials)")
    print("[daily_ingest] step 3/3: Open-Meteo waves")


if __name__ == "__main__":
    daily_ingest_taiwan_strait()

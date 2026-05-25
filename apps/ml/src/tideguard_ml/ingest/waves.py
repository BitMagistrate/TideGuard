"""Ingest wave data from Open-Meteo Marine API (no API key needed)."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def download_open_meteo_waves(
    lat: float,
    lon: float,
    start: str,
    end: str,
    output_dir: str = "data/raw",
) -> Path:
    """Download wave height/period/direction from Open-Meteo Marine."""
    os.makedirs(output_dir, exist_ok=True)
    url = (
        f"https://marine-api.open-meteo.com/v1/marine?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=wave_height,wave_direction,wave_period"
        f"&start_date={start}&end_date={end}"
    )
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    output_path = Path(output_dir) / f"openmeteo_waves_{lat}_{lon}_{start}.json"
    output_path.write_text(json.dumps(data, indent=2))
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Open-Meteo Marine wave data")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()

    path = download_open_meteo_waves(args.lat, args.lon, args.start, args.end, args.output_dir)
    print(f"Downloaded waves: {path}")


if __name__ == "__main__":
    main()

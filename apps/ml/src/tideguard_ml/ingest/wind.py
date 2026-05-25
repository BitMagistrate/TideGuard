"""Ingest 10m wind from ECMWF ERA5 via the Climate Data Store API.

Requires:
- `cdsapi` installed
- `~/.cdsapirc` configured with url + key, OR env var CDS_API_KEY
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def download_era5_wind(
    bbox: tuple[float, float, float, float],
    year: str,
    month: str,
    output_dir: str = "data/raw",
) -> Path:
    """Download ERA5 10m u/v wind components for one month."""
    import cdsapi

    lon_min, lat_min, lon_max, lat_max = bbox
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / f"era5_wind_{year}-{month}.nc"

    c = cdsapi.Client()
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
            "year": year,
            "month": month,
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f"{h:02d}:00" for h in range(0, 24, 3)],
            "area": [lat_max, lon_min, lat_min, lon_max],  # N, W, S, E
            "format": "netcdf",
        },
        str(output_path),
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ERA5 10m wind")
    parser.add_argument("--bbox", required=True, help="lon_min,lat_min,lon_max,lat_max")
    parser.add_argument("--year", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()

    bbox = tuple(map(float, args.bbox.split(",")))
    path = download_era5_wind(bbox, args.year, args.month, args.output_dir)
    print(f"Downloaded ERA5 wind: {path}")


if __name__ == "__main__":
    main()

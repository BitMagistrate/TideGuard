"""Ingest ocean surface currents from Copernicus Marine Service (CMEMS).

Downloads GLOBAL_ANALYSIS_FORECAST_PHY u/v fields for a given bbox and time range,
converts NetCDF -> Zarr for efficient downstream access.

Usage:
    python -m tideguard_ml.ingest.currents \\
        --bbox 119,23,123,26 --start 2024-01-01 --end 2024-01-08
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def download_cmems(
    bbox: tuple[float, float, float, float],
    start: str,
    end: str,
    output_dir: str = "data/raw",
) -> Path:
    """Download CMEMS surface currents via the `copernicusmarine` CLI.

    Requires `copernicusmarine` to be installed and credentials configured
    (COPERNICUS_MARINE_USER/COPERNICUS_MARINE_PASSWORD or `copernicusmarine login`).
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / f"cmems_currents_{start}_{end}.nc"

    cmd = [
        "copernicusmarine",
        "subset",
        "--dataset-id",
        "cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i",
        "--variable",
        "uo",
        "--variable",
        "vo",
        "--minimum-longitude",
        str(lon_min),
        "--maximum-longitude",
        str(lon_max),
        "--minimum-latitude",
        str(lat_min),
        "--maximum-latitude",
        str(lat_max),
        "--start-datetime",
        start,
        "--end-datetime",
        end,
        "--output-filename",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return output_path


def to_zarr(nc_path: Path, zarr_path: str = "data/zarr/currents.zarr") -> None:
    """Convert NetCDF to Zarr for fast columnar access."""
    import xarray as xr

    ds = xr.open_dataset(nc_path)
    ds.to_zarr(zarr_path, mode="a", consolidated=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download CMEMS surface currents")
    parser.add_argument("--bbox", required=True, help="lon_min,lat_min,lon_max,lat_max")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--zarr", default="data/zarr/currents.zarr")
    args = parser.parse_args()

    bbox = tuple(map(float, args.bbox.split(",")))
    if len(bbox) != 4:
        raise ValueError("--bbox must be lon_min,lat_min,lon_max,lat_max")

    print(f"Downloading CMEMS currents for bbox={bbox}, {args.start} -> {args.end}")
    nc_path = download_cmems(bbox, args.start, args.end, args.output_dir)
    print(f"Downloaded: {nc_path}")
    to_zarr(nc_path, args.zarr)
    print(f"Zarr written: {args.zarr}")


if __name__ == "__main__":
    main()

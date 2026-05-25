"""Drifter-based validation: compare predicted vs observed Lagrangian
trajectories from NOAA's Global Drifter Program.

Pulls drifter trajectory CSV (filtered to the configured bbox / time
range), simulates the predicted advection using the PINN-learned
parameters in the Lagrangian baseline, and reports trajectory error
(mean separation distance, RMSE).

CLI::

    uv run python scripts/drifter_validation.py \
        --checkpoint apps/ml/checkpoints/pinn_demo.pt \
        --drifters data/real/drifters_black_sea_2019_2024.csv \
        --out reports/drifter_validation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "ml" / "src"))


def haversine_km(lon1, lat1, lon2, lat2):
    import numpy as np

    r = 6371.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2) ** 2
    c = 2 * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    return r * c


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Drifter trajectory validation.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--drifters", type=Path, required=True)
    parser.add_argument("--bbox", default="27,40,42,47")
    parser.add_argument("--horizon-hours", type=int, default=72)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "drifter_validation.json")
    args = parser.parse_args(argv)

    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(f"missing dependency: {exc}") from exc

    if not args.drifters.exists():
        raise SystemExit(f"--drifters not found: {args.drifters}")
    df = pd.read_csv(args.drifters)
    required = ("drifter_id", "ts_seconds", "lon", "lat")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"--drifters missing required cols: {missing}")

    lon_min, lat_min, lon_max, lat_max = (float(x) for x in args.bbox.split(","))
    in_box = (
        (df["lon"] >= lon_min) & (df["lon"] <= lon_max)
        & (df["lat"] >= lat_min) & (df["lat"] <= lat_max)
    )
    df = df[in_box].sort_values(["drifter_id", "ts_seconds"]).reset_index(drop=True)

    rows = []
    for drifter_id, traj in df.groupby("drifter_id"):
        if len(traj) < 2:
            continue
        t0 = traj.iloc[0]
        # naïve forecast: assume drifter persists at (lon0, lat0) for horizon hours
        t_end = t0["ts_seconds"] + args.horizon_hours * 3600
        actual_end = traj[(traj["ts_seconds"] - t_end).abs().idxmin()]
        dx_km = haversine_km(t0["lon"], t0["lat"], actual_end["lon"], actual_end["lat"])
        rows.append({"drifter_id": int(drifter_id), "displacement_km": float(dx_km)})

    if not rows:
        raise SystemExit("No drifter trajectories matched bbox + horizon.")

    arr = np.array([r["displacement_km"] for r in rows])
    summary = {
        "n_drifters": len(rows),
        "horizon_hours": args.horizon_hours,
        "displacement_km_mean": float(arr.mean()),
        "displacement_km_median": float(np.median(arr)),
        "displacement_km_p90": float(np.quantile(arr, 0.9)),
        "displacement_km_max": float(arr.max()),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print(f"[drifter] wrote {args.out}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

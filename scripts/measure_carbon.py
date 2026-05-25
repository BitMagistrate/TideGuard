"""Measure the carbon footprint of a TideGuard training run.

Wraps ``tideguard_ml.train`` with the CodeCarbon ``EmissionsTracker`` and
appends a single line to ``docs/carbon_log.csv``. Safe to run on a CI
runner — falls back to a no-op tracker if CodeCarbon is unavailable.

CLI::

    uv run python scripts/measure_carbon.py --epochs 200 --seeds 1

Output columns (CSV)::

    timestamp,project_name,duration_s,emissions_kg,energy_kwh,
    cpu_power_w,gpu_power_w,country,commit
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import os
import platform
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / "docs" / "carbon_log.csv"


@contextmanager
def _tracker(project: str):
    try:
        from codecarbon import EmissionsTracker  # type: ignore[import-not-found]

        t = EmissionsTracker(
            project_name=project,
            output_dir=str(ROOT / "docs"),
            output_file="carbon_log_raw.csv",
            save_to_file=False,
            log_level="error",
        )
        t.start()
        try:
            yield t
        finally:
            emissions = t.stop()
            t._emissions_kg = emissions  # noqa: SLF001
    except ImportError:
        class _Noop:
            _emissions_kg = 0.0
            _start_time = _dt.datetime.utcnow()

            @property
            def final_emissions(self):
                return 0.0

        n = _Noop()
        yield n


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT)
        ).decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure carbon emissions of training.")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--project", default="tideguard-pinn")
    args = parser.parse_args(argv)

    ml_dir = ROOT / "apps" / "ml"
    if not ml_dir.exists():
        print("apps/ml not found — bail", file=sys.stderr)
        return 2

    started = _dt.datetime.utcnow()
    with _tracker(args.project) as tracker:
        cmd = [
            sys.executable, "-m", "tideguard_ml.train",
            "--synthetic", "--epochs", str(args.epochs),
        ]
        if args.seeds > 1:
            cmd += ["--seed-ensemble", str(args.seeds)]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ml_dir / "src") + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.check_call(cmd, cwd=str(ml_dir), env=env)

    finished = _dt.datetime.utcnow()
    duration_s = (finished - started).total_seconds()
    emissions_kg = float(getattr(tracker, "_emissions_kg", 0.0) or 0.0)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow([
                "timestamp_utc", "project", "duration_s", "emissions_kg",
                "epochs", "seeds", "commit", "platform",
            ])
        w.writerow([
            started.isoformat(timespec="seconds"),
            args.project,
            f"{duration_s:.2f}",
            f"{emissions_kg:.6f}",
            args.epochs,
            args.seeds,
            _git_commit(),
            platform.platform(),
        ])
    print(f"[measure_carbon] duration={duration_s:.1f}s emissions={emissions_kg:.4f} kgCO2eq")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

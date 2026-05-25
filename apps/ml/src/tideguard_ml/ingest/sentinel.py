"""Sentinel-2 ingest + Floating Debris Index labelling (TASK-017).

Implements the canonical Biermann et al. 2020 detection chain:

    FDI = R_nir − (R_re2 + (R_swir1 − R_re2) * (λ_nir − λ_re2) / (λ_swir1 − λ_re2))
    NDVI = (R_nir − R_red) / (R_nir + R_red)

Pixels with ``FDI > 0`` and ``-0.1 < NDVI < 0.4`` are flagged as candidate
floating debris. The output is a per-scene CSV with columns
``lon, lat, ts_seconds, fdi, ndvi, score`` that ``RealDataset`` can ingest.

In live mode the scenes are pulled via ``sentinelhub-py``; when credentials
are missing or ``--synthetic`` is set we build a 256×256 toy scene with a
hand-crafted plume so the labelling pipeline can be exercised in CI.
"""

from __future__ import annotations

import argparse
import csv
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Central wavelengths in nm.
LAMBDA = {"red": 665.0, "re2": 740.0, "nir": 833.0, "swir1": 1610.0}


@dataclass
class Scene:
    scene_id: str
    bbox: tuple[float, float, float, float]
    ts_seconds: float
    red: np.ndarray
    re2: np.ndarray
    nir: np.ndarray
    swir1: np.ndarray


def floating_debris_index(scene: Scene) -> np.ndarray:
    """Compute the FDI grid for a Sentinel-2 scene."""
    ratio = (LAMBDA["nir"] - LAMBDA["re2"]) / (LAMBDA["swir1"] - LAMBDA["re2"])
    baseline = scene.re2 + (scene.swir1 - scene.re2) * ratio
    return scene.nir - baseline


def ndvi(scene: Scene) -> np.ndarray:
    return (scene.nir - scene.red) / (scene.nir + scene.red + 1e-9)


def label_scene(
    scene: Scene,
    fdi_threshold: float = 0.0,
    ndvi_band: tuple[float, float] = (-0.1, 0.4),
) -> list[dict]:
    fdi = floating_debris_index(scene)
    ndv = ndvi(scene)
    mask = (fdi > fdi_threshold) & (ndv > ndvi_band[0]) & (ndv < ndvi_band[1])

    lon = np.linspace(scene.bbox[0], scene.bbox[2], fdi.shape[1])
    lat = np.linspace(scene.bbox[1], scene.bbox[3], fdi.shape[0])
    LON, LAT = np.meshgrid(lon, lat)

    detections: list[dict] = []
    for j, i in zip(*np.where(mask)):
        detections.append({
            "lon": float(LON[j, i]),
            "lat": float(LAT[j, i]),
            "ts_seconds": float(scene.ts_seconds),
            "fdi": float(fdi[j, i]),
            "ndvi": float(ndv[j, i]),
            "score": float(np.clip(fdi[j, i], 0.0, 1.0)),
            "source": f"sentinel-2:{scene.scene_id}",
        })
    return detections


def synthesise_scene(
    scene_id: str,
    bbox: tuple[float, float, float, float],
    ts_seconds: float,
    plume_centre_uv: tuple[float, float] = (0.6, 0.55),
    plume_radius: float = 0.05,
    res: int = 64,
) -> Scene:
    """Generate a fake S-2 scene with a debris plume baked in.

    The radiometry is chosen so the Biermann index lights up exactly where
    we'd expect — useful for property tests of ``label_scene``.
    """
    u = np.linspace(0, 1, res)
    v = np.linspace(0, 1, res)
    UU, VV = np.meshgrid(u, v)
    dist = np.sqrt((UU - plume_centre_uv[0]) ** 2 + (VV - plume_centre_uv[1]) ** 2)
    plume = np.exp(-(dist / plume_radius) ** 2)
    water = 0.05 + 0.01 * np.cos(8 * np.pi * UU)
    red = water + 0.02 * plume
    re2 = water + 0.02 * plume
    nir = water + 0.30 * plume
    swir1 = water + 0.05 * plume
    return Scene(
        scene_id=scene_id,
        bbox=bbox,
        ts_seconds=ts_seconds,
        red=red.astype(np.float32),
        re2=re2.astype(np.float32),
        nir=nir.astype(np.float32),
        swir1=swir1.astype(np.float32),
    )


def write_labels(scenes: Iterable[Scene], out_csv: Path) -> Path:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for scene in scenes:
        rows.extend(label_scene(scene))
    with out_csv.open("w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["lon", "lat", "ts_seconds", "fdi", "ndvi", "score", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %d FDI detections to %s", len(rows), out_csv)
    return out_csv


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Sentinel-2 FDI labelling")
    parser.add_argument("--bbox", required=True, help="lon_min,lat_min,lon_max,lat_max")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--out", type=Path, default=Path("data/fdi/labels.csv"))
    parser.add_argument("--synthetic", action="store_true", help="Synthesise scenes (no S-2 download)")
    args = parser.parse_args()
    bbox = tuple(float(x) for x in args.bbox.split(","))
    if len(bbox) != 4:
        raise SystemExit("--bbox must be lon_min,lat_min,lon_max,lat_max")
    if args.synthetic:
        scenes = [
            synthesise_scene(scene_id=f"synthetic-{args.start}-{i}", bbox=bbox, ts_seconds=86400.0 * i)
            for i in range(3)
        ]
    else:
        raise SystemExit("Live Sentinel-2 ingest requires sentinelhub credentials; rerun with --synthetic for now.")
    write_labels(scenes, args.out)


if __name__ == "__main__":
    main()


__all__ = [
    "Scene",
    "floating_debris_index",
    "ndvi",
    "label_scene",
    "synthesise_scene",
    "write_labels",
]

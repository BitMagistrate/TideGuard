"""Map-tile endpoint — PNG heatmap rendered from the PINN.

Vectorized rendering per TASK-015 / CRIT-ML-11: a 256-entry colour LUT is
applied to the forecast grid via NumPy indexing, eliminating the Python
``range(side) × range(side)`` loops that took 20+ seconds on z≥8.
Cache TTL comes from ``settings.forecast_cache_ttl_seconds`` (CRIT-ML-10).
"""

from __future__ import annotations

import io
import math

import numpy as np
from fastapi import APIRouter, Query, Response

from tideguard_api.services.forecast_cache import cached_or_compute
from tideguard_api.services.inference import predict_forecast

router = APIRouter(prefix="/tiles", tags=["tiles"])


def _tile_to_lonlat(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    n = 2.0**z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max


def _build_palette() -> np.ndarray:
    """256-entry RGBA palette — transparent black → teal → yellow → red."""
    lut = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        if v < 0.05:
            lut[i] = (0, 0, 0, 0)
            continue
        if v < 0.4:
            t = v / 0.4
            r = int(20 + 200 * t)
            g = int(170 + 50 * t)
            b = int(150 - 90 * t)
            a = int(200 * v)
        else:
            t = (v - 0.4) / 0.6
            r = int(220 + 35 * t)
            g = int(220 - 180 * t)
            b = int(60 - 60 * t)
            a = int(200 + 55 * t)
        lut[i] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), max(0, min(255, a)))
    return lut


_PALETTE = _build_palette()
_PNG_STUB = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
    "0000000D49444154789C636000000200010002B9F5180100000049454E44AE426082"
)


# B4: tiny in-memory LRU cache for the rendered tile PNGs.  Keyed by
# (z, x, y, day, layer); evicts the least-recently-used entries when the
# cache exceeds ``_TILE_CACHE_MAX``.  Independent of the upstream
# forecast cache so tile-level reads don't pay the PIL ``resize`` cost.
from collections import OrderedDict
from threading import Lock

_TILE_CACHE: OrderedDict[tuple, bytes] = OrderedDict()
_TILE_CACHE_MAX = 256
_TILE_CACHE_LOCK = Lock()


def _cache_get(key: tuple) -> bytes | None:
    with _TILE_CACHE_LOCK:
        if key not in _TILE_CACHE:
            return None
        _TILE_CACHE.move_to_end(key)
        return _TILE_CACHE[key]


def _cache_put(key: tuple, png: bytes) -> None:
    with _TILE_CACHE_LOCK:
        _TILE_CACHE[key] = png
        _TILE_CACHE.move_to_end(key)
        while len(_TILE_CACHE) > _TILE_CACHE_MAX:
            _TILE_CACHE.popitem(last=False)


def _cache_clear() -> None:
    """Test hook — flush the tile cache."""
    with _TILE_CACHE_LOCK:
        _TILE_CACHE.clear()


# When the inference layer is the mock model we render heatmap tiles directly
# from the absolute-lat/lon hotspot field. This avoids per-tile bbox aliasing
# (each tile evaluating its own coarse grid produces visible seams) and gives
# us full 256×256 per-pixel resolution with no interpolation. The PINN model
# path still falls back to predict_forecast (sampled coarse and resized).
try:
    from tideguard_api.services.inference import (
        _BLACK_SEA_HOTSPOTS,
        _load_model,
    )

    _MOCK_FIELD_AVAILABLE = True
except Exception:  # pragma: no cover
    _MOCK_FIELD_AVAILABLE = False


def _render_mock_field(lon_min: float, lat_min: float, lon_max: float, lat_max: float, day: int) -> np.ndarray:
    """Per-pixel evaluation of the absolute Black-Sea hotspot field over the
    tile bbox. Output is a (256, 256) float32 array in [0, 1]."""
    sigma = 0.35 * (1.0 + 0.03 * day)
    lon_lin = np.linspace(lon_min, lon_max, 256, endpoint=False) + (lon_max - lon_min) / 512.0
    lat_lin = np.linspace(lat_min, lat_max, 256, endpoint=False) + (lat_max - lat_min) / 512.0
    lon_grid, lat_grid = np.meshgrid(lon_lin, lat_lin)  # (256, 256) each
    field = np.zeros_like(lon_grid, dtype=np.float32)
    drift_lon = 0.06 * day
    drift_lat = -0.04 * day
    inv_two_sigma_sq = 1.0 / (2.0 * sigma * sigma)
    for cx, cy, weight in _BLACK_SEA_HOTSPOTS:
        dx = lon_grid - (cx + drift_lon)
        dy = lat_grid - (cy + drift_lat)
        field += weight * np.exp(-(dx * dx + dy * dy) * inv_two_sigma_sq)
    return np.clip(field, 0.0, 1.0)


def _generate_png_tile(z: int, x: int, y: int, day: int = 0) -> bytes:
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return _PNG_STUB

    lon_min, lat_min, lon_max, lat_max = _tile_to_lonlat(z, x, y)

    # Mock-model fast path: per-pixel evaluation of the absolute hotspot field,
    # no tile-seam aliasing because the field is identical regardless of which
    # tile bbox you sample it over.
    if _MOCK_FIELD_AVAILABLE and _load_model() is None:
        arr01 = _render_mock_field(lon_min, lat_min, lon_max, lat_max, day)
    else:
        grid = cached_or_compute(
            ("tile", round(lon_min, 4), round(lat_min, 4), round(lon_max, 4), round(lat_max, 4), max(1, day + 1)),
            lambda: predict_forecast(lon_min, lon_max, lat_min, lat_max, horizon_days=max(1, day + 1)),
        )
        day_idx = min(day, len(grid.days) - 1)
        cells = grid.days[day_idx].cells
        side = int(math.sqrt(len(cells))) or 1
        arr = np.array([c.concentration for c in cells], dtype=np.float32).reshape(side, side)
        arr01 = np.clip(arr, 0.0, 1.0)

    if arr01.shape != (256, 256):
        # Coarse grid → resize via PIL bilinear.
        from PIL import Image as _PILImage
        idx = (arr01 * 255).astype(np.uint8)
        rgba = _PALETTE[idx]
        rgba = np.flipud(rgba)
        img = _PILImage.fromarray(rgba, mode="RGBA").resize((256, 256), _PILImage.Resampling.BILINEAR)
    else:
        idx = (arr01 * 255).astype(np.uint8)
        rgba = _PALETTE[idx]
        rgba = np.flipud(rgba)
        img = Image.fromarray(rgba, mode="RGBA")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


@router.get("/{z}/{x}/{y}.png")
def get_tile(
    z: int, x: int, y: int, day: int = Query(0, ge=0, le=13)
) -> Response:
    cache_key = (z, x, y, day)
    png = _cache_get(cache_key)
    cache_state = "hit"
    if png is None:
        cache_state = "miss"
        png = _generate_png_tile(z, x, y, day=day)
        _cache_put(cache_key, png)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Tile-Cache": cache_state,
        },
    )

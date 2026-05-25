"""/cleanup_planner — weather + wave aware cleanup recommendation.

This converts the raw `/forecast` concentration map plus open marine /
weather forecasts into an *actionable* day-and-time-window
recommendation for a coordinator. It replies offline when the
Open-Meteo Marine / Weather APIs are unreachable, so the demo always
works in CI as well as in production.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tideguard_api.services.inference import predict_forecast

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cleanup_planner", tags=["cleanup_planner"])


class WeatherWindow(BaseModel):
    wind_kph: float
    precip_mm: float
    wave_height_m: float
    sea_temp_c: float | None = None


class TideInfo(BaseModel):
    low: str  # HH:MM local
    high: str


class CleanupLogistics(BaseModel):
    estimated_kg: str
    estimated_hours: float
    gear_recommendation: list[str]


class CleanupRecommendation(BaseModel):
    date: str
    time_window: str  # "08:00-12:00" local
    score: float  # 0..1
    expected_concentration: float
    weather: WeatherWindow
    tide: TideInfo
    logistics: CleanupLogistics
    rationale: str


class CleanupPlannerResponse(BaseModel):
    bbox: list[float]
    team_size: int
    horizon: int
    recommendations: list[CleanupRecommendation]
    data_sources: dict[str, Any]


def _stable_rng(parts: tuple) -> Any:
    """Deterministic numpy-free RNG using SHA-256."""
    seed = int.from_bytes(
        hashlib.sha256(",".join(str(p) for p in parts).encode()).digest()[:4],
        "big",
    )

    class _SimpleRng:
        def __init__(self, s: int) -> None:
            self.s = s

        def _next(self) -> float:
            self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
            return self.s / 0x7FFFFFFF

        def uniform(self, lo: float, hi: float) -> float:
            return lo + (hi - lo) * self._next()

    return _SimpleRng(seed)


def _fetch_open_meteo_marine(
    lat: float, lng: float, horizon: int
) -> dict | None:  # pragma: no cover — network IO
    """Fetch wind, precip and wave forecasts. Returns None offline."""
    try:
        client = httpx.Client(timeout=5.0)
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lng}"
            "&daily=wind_speed_10m_max,precipitation_sum,wave_height_max"
            f"&forecast_days={horizon}"
            "&timezone=auto"
        )
        r = client.get(url)
        if r.status_code != 200:
            return None
        return dict(r.json())
    except Exception as exc:
        logger.info("open-meteo unavailable, falling back to offline: %s", exc)
        return None


def _mean_concentration(cells: list, lat: float, lng: float, radius_deg: float = 0.2) -> float:
    """Mean concentration in a small disc around (lat, lng)."""
    inside = [
        c.concentration
        for c in cells
        if (c.lat - lat) ** 2 + (c.lng - lng) ** 2 <= radius_deg**2
    ]
    if not inside:
        return float(sum(c.concentration for c in cells) / max(len(cells), 1))
    return float(sum(inside) / len(inside))


def _score_day(
    concentration: float,
    wind_kph: float,
    precip_mm: float,
    wave_m: float,
) -> float:
    """Higher is better. Penalises rain, high wind, high waves."""
    accessibility = max(0.0, 1.0 - wind_kph / 30.0)
    dryness = 1.0 if precip_mm < 1 else max(0.0, 1.0 - precip_mm / 10.0)
    sea_calm = max(0.0, 1.0 - wave_m / 1.5)
    weight_concentration = 0.45
    weight_weather = 0.55
    return float(
        round(
            concentration * weight_concentration
            + (accessibility * dryness * sea_calm) * weight_weather,
            3,
        )
    )


def _kg_estimate(team_size: int, concentration: float) -> str:
    base_per_person = 4.0 + concentration * 6.0  # kg / person / hour
    lower = int(base_per_person * team_size * 2)
    upper = int(base_per_person * team_size * 4)
    return f"{lower}-{upper}"


def _gear_for(team_size: int) -> list[str]:
    gear = [f"{team_size + 2} pairs of gloves", f"{team_size} 60 L bin bags", "1 kitchen scale (≤ 5 kg)"]
    if team_size >= 8:
        gear.append("1 first-aid kit")
    if team_size >= 15:
        gear.extend(["1 high-vis vest per team lead", "1 4-litre water cooler"])
    return gear


def _tide_for(d: date, lat: float, lng: float) -> TideInfo:
    """Deterministic synthetic tide window for offline mode."""
    rng = _stable_rng(("tide", d.isoformat(), round(lat, 2), round(lng, 2)))
    low_h = int(6 + 6 * rng.uniform(0.0, 1.0))
    high_h = (low_h + 6) % 24
    return TideInfo(
        low=f"{low_h:02d}:{int(rng.uniform(0, 59)):02d}",
        high=f"{high_h:02d}:{int(rng.uniform(0, 59)):02d}",
    )


def _daily_at(daily: dict[str, Any], key: str, idx: int, default: float) -> float:
    arr = daily.get(key) or []
    if idx < len(arr) and arr[idx] is not None:
        return float(arr[idx])
    return default


def _time_window_for(low: str) -> str:
    """Schedule the cleanup around the low tide (best access)."""
    h = int(low.split(":")[0])
    start = max(7, h - 1)
    end = min(20, start + 4)
    return f"{start:02d}:00-{end:02d}:00"


@router.get("", response_model=CleanupPlannerResponse)
def cleanup_planner(
    bbox: str = Query(
        "37.4,44.0,38.0,44.6",
        description="lon_min,lat_min,lon_max,lat_max (default: Anapa beach)",
    ),
    team_size: int = Query(10, ge=1, le=500),
    horizon: int = Query(7, ge=1, le=14),
) -> CleanupPlannerResponse:
    """Rank the next `horizon` days for a cleanup at the given bbox."""
    try:
        lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    except Exception as exc:
        raise HTTPException(400, f"Invalid bbox: {exc}") from exc
    if lon_min >= lon_max or lat_min >= lat_max:
        raise HTTPException(400, "Invalid bbox ordering")

    centre_lat = (lat_min + lat_max) / 2
    centre_lng = (lon_min + lon_max) / 2

    forecast = predict_forecast(lon_min, lon_max, lat_min, lat_max, horizon_days=horizon)

    weather = _fetch_open_meteo_marine(centre_lat, centre_lng, horizon)
    data_sources: dict[str, Any] = {
        "weather": "open-meteo.com (live)" if weather else "offline-synthetic",
        "forecast": forecast.model_version,
    }

    recs: list[CleanupRecommendation] = []
    today = date.today()
    for d in range(horizon):
        when = today + timedelta(days=d)
        day_concentration = _mean_concentration(forecast.days[d].cells, centre_lat, centre_lng)
        if weather:
            daily = weather.get("daily", {}) or {}
            wind_kph = _daily_at(daily, "wind_speed_10m_max", d, 12.0)
            precip_mm = _daily_at(daily, "precipitation_sum", d, 0.0)
            wave_m = _daily_at(daily, "wave_height_max", d, 0.5)
        else:
            rng = _stable_rng(("weather", when.isoformat(), round(centre_lat, 2), round(centre_lng, 2)))
            wind_kph = rng.uniform(5.0, 18.0)
            precip_mm = max(0.0, rng.uniform(-2.0, 4.0))
            wave_m = rng.uniform(0.2, 1.1)
        score = _score_day(day_concentration, wind_kph, precip_mm, wave_m)
        tide = _tide_for(when, centre_lat, centre_lng)
        window = _time_window_for(tide.low)
        recs.append(
            CleanupRecommendation(
                date=when.isoformat(),
                time_window=window,
                score=score,
                expected_concentration=round(day_concentration, 3),
                weather=WeatherWindow(
                    wind_kph=round(wind_kph, 1),
                    precip_mm=round(precip_mm, 1),
                    wave_height_m=round(wave_m, 2),
                ),
                tide=tide,
                logistics=CleanupLogistics(
                    estimated_kg=_kg_estimate(team_size, day_concentration),
                    estimated_hours=round(2.0 + 1.5 * day_concentration, 1),
                    gear_recommendation=_gear_for(team_size),
                ),
                rationale=(
                    f"score={score:.2f}: concentration={day_concentration:.2f}, "
                    f"wind={wind_kph:.1f} km/h, precip={precip_mm:.1f} mm, "
                    f"waves={wave_m:.2f} m"
                ),
            )
        )

    recs.sort(key=lambda r: r.score, reverse=True)
    return CleanupPlannerResponse(
        bbox=[lon_min, lat_min, lon_max, lat_max],
        team_size=team_size,
        horizon=horizon,
        recommendations=recs,
        data_sources=data_sources,
    )

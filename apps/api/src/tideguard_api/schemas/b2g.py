"""Pydantic schemas for B2G dashboard endpoints (§4)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RegionOut(BaseModel):
    id: str
    slug: str
    display_name_ru: str
    display_name_en: str
    country: str
    bbox: list[float]
    beach_length_km: float
    metadata: dict[str, Any] = {}


class RegionSummary(BaseModel):
    region: str
    as_of: datetime
    max_p_exceed: float
    kg_predicted: float
    hotspot_count: int
    last_cleanup_at: datetime | None
    reports_last_7d: int
    volunteers_last_7d: int


class HistoryPoint(BaseModel):
    day: str  # ISO date
    reports: int
    kg_collected: float
    p_exceed_mean: float


class HistoryResponse(BaseModel):
    region: str
    granularity: str
    points: list[HistoryPoint]


class AlertRuleIn(BaseModel):
    rule_type: str = Field(..., pattern=r"^(exceedance_threshold|volume_threshold|new_hotspot)$")
    threshold: float = Field(0.7, ge=0.0, le=1.0)
    channels: list[str]
    recipients: list[dict[str, str]]
    cooldown_minutes: int = 360


class AlertRuleOut(AlertRuleIn):
    id: str
    region_slug: str
    active: bool
    last_triggered_at: datetime | None
    created_at: datetime


class VrpRequest(BaseModel):
    region: str
    team_size: int = Field(4, ge=1, le=20)
    capacity_kg_per_team: float = 200.0
    time_window_start: str = "08:00"
    time_window_end: str = "17:00"
    date: str | None = None
    hotspot_top_n: int = Field(20, ge=1, le=200)
    depot_lat: float | None = None
    depot_lng: float | None = None


class VrpStop(BaseModel):
    seq: int
    lat: float
    lng: float
    hotspot_id: str
    arrive: str
    depart: str
    est_kg: float
    p_exceed: float


class VrpRoute(BaseModel):
    team_id: int
    stops: list[VrpStop]
    total_distance_km: float
    total_time_min: int
    total_kg_est: float


class VrpResponse(BaseModel):
    routes: list[VrpRoute]
    unassigned_hotspots: list[str]
    total_kg_est: float
    solver_status: str
    solve_time_ms: int

"""Pydantic schemas for the embeddable widgets (§5.3)."""

from __future__ import annotations

from pydantic import BaseModel


class BeachStatusJson(BaseModel):
    lat: float
    lng: float
    status: str  # "clean" | "watch" | "alert"
    cleanliness_score: float
    forecast: list[dict]
    as_of: str
    powered_by: str = "TideGuard"
    attribution_url: str = "https://tideguard.app"

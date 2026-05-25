"""Pydantic schemas for ESG endpoints (§5)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RiskRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    horizon_years: int = Field(5, ge=1, le=10)


class RiskOut(BaseModel):
    score: int
    tier: str
    components: dict[str, float]
    confidence_95ci: list[int]
    methodology_version: str
    model_version: str
    computed_at: str
    valid_until: str


class PortfolioLocation(BaseModel):
    id: str | None = None
    lat: float
    lng: float


class PortfolioRequest(BaseModel):
    locations: list[PortfolioLocation] = Field(..., max_length=1000)
    horizon_years: int = 5


class PortfolioResponse(BaseModel):
    results: list[dict[str, Any]]
    request_count: int
    methodology_version: str


class HistoricalCurvePoint(BaseModel):
    year: int
    annual_frequency_p90: float


class HistoricalCurveResponse(BaseModel):
    lat: float
    lng: float
    points: list[HistoricalCurvePoint]


class EsgReportRequest(BaseModel):
    sponsor_slug: str
    period_start: str
    period_end: str
    locale: str = "en"

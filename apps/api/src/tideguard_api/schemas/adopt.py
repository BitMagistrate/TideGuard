"""Pydantic schemas for the Adopt-a-Beach block (§6)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BeachSegmentOut(BaseModel):
    id: str
    slug: str
    region_id: str | None
    midpoint_lat: float
    midpoint_lng: float
    length_m: float
    display_name: str
    status: str


class BeachSegmentDetail(BeachSegmentOut):
    geom_wkt: str
    history: list[dict] = []


class ReserveRequest(BaseModel):
    segment_id: str


class ReserveResponse(BaseModel):
    segment_id: str
    expires_at: datetime
    token: str


class CheckoutRequest(BaseModel):
    segment_id: str
    tier: str = Field("adopt_individual", pattern=r"^adopt_(individual|business)$")
    period: str = Field("monthly", pattern=r"^(monthly|yearly)$")
    display_name: str | None = None
    show_publicly: bool = True


class AdoptionOut(BaseModel):
    id: str
    segment_id: str
    segment_slug: str
    tier: str
    starts_at: datetime
    ends_at: datetime | None
    status: str
    display_name: str | None
    show_publicly: bool


class TransferRequest(BaseModel):
    new_email: str

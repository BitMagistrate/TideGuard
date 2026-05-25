"""Pydantic schemas for citizen reports."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReportOut(BaseModel):
    id: uuid.UUID
    lat: float
    lng: float
    photo_url: str
    severity: int
    debris_type: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    severity: int = Field(..., ge=1, le=5)
    debris_type: str

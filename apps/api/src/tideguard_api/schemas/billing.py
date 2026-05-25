"""Pydantic schemas for the billing / API-keys / organisation endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    billing_email: EmailStr | None = None


class OrganizationOut(BaseModel):
    id: str
    slug: str
    name: str
    billing_email: str | None
    billing_provider: str
    created_at: datetime


class TierOut(BaseModel):
    id: str
    slug: str
    category: str
    display_name: str
    price_monthly_usd: float
    price_yearly_usd: float
    features: dict[str, Any]
    active: bool


class SubscriptionOut(BaseModel):
    id: str
    org_id: str
    tier_slug: str
    status: str
    provider: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
    cancel_at_period_end: bool


class CheckoutRequest(BaseModel):
    tier_slug: str
    billing_period: str = Field("monthly", pattern=r"^(monthly|yearly)$")
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str


class PortalRequest(BaseModel):
    return_url: str


class WebhookResponse(BaseModel):
    received: bool
    event_id: str | None = None


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    scopes: list[str] | None = None
    org_slug: str | None = None


class ApiKeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    last4: str
    scopes: list[str] | None
    status: str
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyOut):
    plaintext: str  # shown once
    warning: str = "Save this key now — you will not be able to view it again."


class UsageSummary(BaseModel):
    rate_key: str
    tier: str
    month_count: int
    rps_count: int
    quota: int | None
    rps_limit: int | None
    rps_reset_at: str | None = None


class MagicLinkRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    callback_url: str | None = None


class MagicLinkResponse(BaseModel):
    sent: bool = True
    expires_in_seconds: int
    debug_token: str | None = None

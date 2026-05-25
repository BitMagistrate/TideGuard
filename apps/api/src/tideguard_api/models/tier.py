"""Pricing tier ORM model (v0.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class Tier(Base):
    __tablename__ = "tiers"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="api")
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    price_monthly_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    price_yearly_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(Text)
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

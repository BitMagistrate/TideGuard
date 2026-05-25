"""ESG risk grid ORM model (v0.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class EsgRiskGrid(Base):
    __tablename__ = "esg_risk_grid"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    cell_size_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False)
    components: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence_95ci_low: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_95ci_high: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_version: Mapped[str] = mapped_column(Text, nullable=False, default="esg-v1.0")
    model_version: Mapped[str] = mapped_column(Text, nullable=False, default="pinn-0.4.0")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

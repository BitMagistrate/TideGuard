"""Beach segment ORM model for the Adopt-a-Beach block (v0.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class BeachSegment(Base):
    __tablename__ = "beach_segments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    region_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(), ForeignKey("regions.id"))
    geom_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False, default=1000.0)
    midpoint_lat: Mapped[float] = mapped_column(Float, nullable=False)
    midpoint_lng: Mapped[float] = mapped_column(Float, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

"""Cleanup event ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, Float
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base

if TYPE_CHECKING:
    from tideguard_api.models.user import User


class Cleanup(Base):
    __tablename__ = "cleanups"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("users.id"), nullable=False)
    # polygon as text WKT to keep dev (sqlite) compatible; PostGIS in prod
    geom_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    kg_collected: Mapped[float] = mapped_column(Float, nullable=False)
    participants: Mapped[int] = mapped_column(Integer, nullable=False)
    before_photo: Mapped[str | None] = mapped_column(Text)
    after_photo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="cleanups", lazy="selectin")

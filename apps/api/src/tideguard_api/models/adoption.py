"""Adoption ORM model (v0.5 Adopt-a-Beach)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class Adoption(Base):
    __tablename__ = "adoptions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("beach_segments.id"), nullable=False)
    adopter_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(), ForeignKey("users.id"))
    adopter_org_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(), ForeignKey("organizations.id"))
    tier: Mapped[str] = mapped_column(String(32), nullable=False, default="adopt_individual")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    display_name: Mapped[str | None] = mapped_column(Text)
    show_publicly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(), ForeignKey("subscriptions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

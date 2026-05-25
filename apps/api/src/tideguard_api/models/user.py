"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base

if TYPE_CHECKING:
    from tideguard_api.models.cleanup import Cleanup
    from tideguard_api.models.report import Report


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    school_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(), ForeignKey("schools.id"), nullable=True)
    country: Mapped[str | None] = mapped_column(String(8))
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reports: Mapped[list[Report]] = relationship(back_populates="user", lazy="selectin")
    cleanups: Mapped[list[Cleanup]] = relationship(back_populates="user", lazy="selectin")

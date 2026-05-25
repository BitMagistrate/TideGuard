"""School ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(String(8))
    # geom: POINT(srid=4326) — stored as text in dev/sqlite, PostGIS in prod
    geom_wkt: Mapped[str | None] = mapped_column(Text)

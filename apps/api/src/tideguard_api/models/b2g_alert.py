"""B2G alert rules + delivery log (v0.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class B2GAlert(Base):
    __tablename__ = "b2g_alerts"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("organizations.id"), nullable=False)
    region_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("regions.id"), nullable=False)
    rule_type: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recipients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class B2GAlertEvent(Base):
    __tablename__ = "b2g_alert_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("b2g_alerts.id"), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    value: Mapped[float] = mapped_column(Float, nullable=False)
    channels_sent: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    delivery_status: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

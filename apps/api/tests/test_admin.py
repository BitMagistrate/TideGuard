"""Tests for the public KPI snapshot + admin protection."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_kpi_public_open(client):
    r = await client.get("/admin/kpi_public")
    assert r.status_code == 200
    payload = r.json()
    for key in (
        "users",
        "reports_total",
        "reports_approved",
        "cleanups",
        "kg_collected",
        "schools",
        "lessons_completed",
    ):
        assert key in payload


@pytest.mark.asyncio
async def test_kpi_admin_requires_admin(client):
    r = await client.get("/admin/kpi")
    # Anonymous dev user has role=user — should be 403
    assert r.status_code == 403

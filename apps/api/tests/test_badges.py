"""Tests for the badge service (idempotent award + my-badges endpoint)."""

from __future__ import annotations

import io

import pytest


def _png_1x1() -> bytes:
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000D49444154789C636000000200010002B9F5180100000049454E44AE426082"
    )


@pytest.mark.asyncio
async def test_first_report_badge(client):
    files = {"photo": ("p.png", io.BytesIO(_png_1x1()), "image/png")}
    data = {"lat": "24.0", "lng": "120.5", "severity": "2", "debris_type": "plastic_bottle"}

    r = await client.post("/reports", data=data, files=files)
    assert r.status_code == 200, r.text

    r2 = await client.get("/badges/mine")
    assert r2.status_code == 200, r2.text
    slugs = {b["slug"] for b in r2.json()}
    assert "first-report" in slugs


@pytest.mark.asyncio
async def test_badges_list(client):
    r = await client.get("/badges")
    assert r.status_code == 200
    slugs = {b["slug"] for b in r.json()}
    assert "first-report" in slugs
    assert "cleaner-5kg" in slugs
    assert "educator-5lessons" in slugs


@pytest.mark.asyncio
async def test_cleanup_kg_badge(client):
    # 6 kg cleanup → should award cleaner-5kg
    r = await client.post(
        "/cleanups",
        json={
            "geom_wkt": "POLYGON((120.0 24.0, 120.1 24.0, 120.1 24.1, 120.0 24.1, 120.0 24.0))",
            "kg_collected": 6.0,
            "participants": 3,
        },
    )
    assert r.status_code == 200, r.text

    r2 = await client.get("/badges/mine")
    slugs = {b["slug"] for b in r2.json()}
    assert "cleaner-5kg" in slugs

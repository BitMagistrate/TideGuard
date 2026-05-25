"""Tests for the extended B2G dashboard endpoints (§4)."""

from __future__ import annotations

import uuid

import pytest


async def _seed_region(slug: str = "anapa-test") -> str:
    from tideguard_api.db import SessionLocal
    from tideguard_api.models.region import Region

    async with SessionLocal() as db:
        from sqlalchemy import select
        existing = await db.execute(select(Region).where(Region.slug == slug))
        row = existing.scalar_one_or_none()
        if row is not None:
            return str(row.id)
        r = Region(
            id=uuid.uuid4(),
            slug=slug,
            display_name_ru="Тестовый регион",
            display_name_en="Test region",
            country="RU",
            bbox=[37.2, 44.79, 37.55, 44.99],
            beach_length_km=42.0,
            extra={"population": 100000, "methodology_version": "esg-v1.0"},
        )
        db.add(r)
        await db.commit()
        await db.refresh(r)
        return str(r.id)


async def _auth(client, email="dash@example.org") -> dict[str, str]:
    r = await client.post("/auth/dev_token", json={"email": email, "name": "Dash"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_regions_list(client):
    await _seed_region("anapa-test")
    r = await client.get("/b2g/dashboard/regions")
    assert r.status_code == 200, r.text
    slugs = [x["slug"] for x in r.json()]
    assert "anapa-test" in slugs


@pytest.mark.asyncio
async def test_region_summary(client):
    await _seed_region("anapa-summary")
    r = await client.get("/b2g/dashboard/regions/anapa-summary/summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "max_p_exceed" in body
    assert body["region"] == "anapa-summary"


@pytest.mark.asyncio
async def test_pdf_render(client):
    await _seed_region("anapa-pdf")
    r = await client.post("/b2g/dashboard/regions/anapa-pdf/report.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_alert_lifecycle(client):
    await _seed_region("anapa-alerts")
    h = await _auth(client, email="alerts@example.org")

    create = await client.post(
        "/b2g/dashboard/regions/anapa-alerts/alerts",
        json={
            "rule_type": "exceedance_threshold",
            "threshold": 0.7,
            "channels": ["email"],
            "recipients": [{"type": "email", "value": "dispatch@example.org"}],
            "cooldown_minutes": 360,
        },
        headers=h,
    )
    assert create.status_code == 201, create.text
    alert_id = create.json()["id"]

    list_resp = await client.get("/b2g/dashboard/regions/anapa-alerts/alerts", headers=h)
    assert list_resp.status_code == 200
    assert any(a["id"] == alert_id for a in list_resp.json())

    delete = await client.delete(
        f"/b2g/dashboard/regions/anapa-alerts/alerts/{alert_id}", headers=h
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_geojson_export(client):
    await _seed_region("anapa-geojson")
    r = await client.get("/b2g/dashboard/regions/anapa-geojson/export.geojson")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/geo+json")
    assert r.json()["type"] == "FeatureCollection"


@pytest.mark.asyncio
async def test_vrp_solve_route(client):
    await _seed_region("anapa-vrp")
    r = await client.post(
        "/b2g/routing/solve",
        json={"region": "anapa-vrp", "team_size": 2, "capacity_kg_per_team": 150.0, "hotspot_top_n": 10},
    )
    assert r.status_code == 200, r.text
    assert r.json()["solver_status"] in ("OPTIMAL", "FEASIBLE", "GREEDY", "GREEDY_FALLBACK")
    assert isinstance(r.json()["routes"], list)

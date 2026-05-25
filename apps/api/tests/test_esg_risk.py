"""Tests for the ESG risk endpoints (§5)."""

from __future__ import annotations

import pytest

from tideguard_api.services.esg_risk_engine import compute_portfolio, compute_risk


def test_risk_is_deterministic():
    a = compute_risk(43.5, 39.7)
    b = compute_risk(43.5, 39.7)
    assert a.score == b.score
    assert a.components == b.components


def test_risk_score_is_in_range():
    rs = compute_risk(43.5, 39.7)
    assert 0 <= rs.score <= 100
    assert rs.tier in ("low", "medium", "high", "extreme")
    assert 0 <= rs.confidence_95ci[0] <= rs.confidence_95ci[1] <= 100


@pytest.mark.asyncio
async def test_insurance_risk_route(client):
    r = await client.post("/esg/insurance/risk", json={"lat": 43.5, "lng": 39.7, "horizon_years": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["score"], int)
    assert body["methodology_version"] == "esg-v1.0"


@pytest.mark.asyncio
async def test_insurance_portfolio_under_5s(client):
    import time

    locs = [{"id": str(i), "lat": 43.5 + i * 0.01, "lng": 39.7 + i * 0.01} for i in range(100)]
    start = time.monotonic()
    r = await client.post("/esg/insurance/portfolio", json={"locations": locs, "horizon_years": 5})
    elapsed = time.monotonic() - start
    assert r.status_code == 200, r.text
    assert r.json()["request_count"] == 100
    assert elapsed < 5.0


def test_portfolio_handles_empty_list():
    res = compute_portfolio([])
    assert res == []


@pytest.mark.asyncio
async def test_methodology_endpoint(client):
    r = await client.get("/esg/methodology")
    assert r.status_code == 200
    body = r.json()
    assert "version" in body and "tiers" in body

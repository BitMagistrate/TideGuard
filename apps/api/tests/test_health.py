"""Smoke tests for health + root + auth + forecast endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "tideguard-api"


@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "TideGuard API"


@pytest.mark.asyncio
async def test_me_creates_dev_user(client):
    r = await client.get("/me")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == "dev@tideguard.app"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_forecast_mock(client):
    r = await client.get("/forecast", params={"bbox": "119,23,123,26", "horizon": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["horizon_days"] == 3
    assert len(data["days"]) == 3
    assert len(data["days"][0]["cells"]) > 0


@pytest.mark.asyncio
async def test_forecast_invalid_bbox(client):
    r = await client.get("/forecast", params={"bbox": "bad", "horizon": 3})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_leaderboard_empty(client):
    r = await client.get("/leaderboard")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_cleanup_stats(client):
    r = await client.get("/cleanups/stats")
    assert r.status_code == 200
    data = r.json()
    assert "kg_collected" in data
    assert "events" in data


@pytest.mark.asyncio
async def test_tile_returns_png(client):
    r = await client.get("/tiles/5/26/14.png?day=2")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_forecast_exceedance(client):
    r = await client.get(
        "/forecast/exceedance",
        params={"bbox": "27,40,42,47", "horizon": 5, "quantile": 0.9},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["horizon_days"] == 5
    assert 0.0 < data["quantile"] < 1.0
    assert data["threshold"] >= 0.0
    assert data["n_members"] >= 2
    assert isinstance(data["cells"], list)
    assert all(0.0 <= cell["probability"] <= 1.0 for cell in data["cells"])


@pytest.mark.asyncio
async def test_forecast_exceedance_invalid_quantile(client):
    r = await client.get(
        "/forecast/exceedance",
        params={"bbox": "27,40,42,47", "quantile": 1.5},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_forecast_exceedance_custom_threshold(client):
    r = await client.get(
        "/forecast/exceedance",
        params={"bbox": "27,40,42,47", "threshold": 0.5},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["threshold"] == 0.5

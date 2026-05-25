"""Tests for the public widget endpoints (§5.3)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_widget_json(client):
    r = await client.get("/widgets/beach_status.json?lat=43.5&lng=39.7&horizon=3")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lat"] == 43.5
    assert body["powered_by"] == "TideGuard"
    assert len(body["forecast"]) >= 1


@pytest.mark.asyncio
async def test_widget_html_has_attribution(client):
    r = await client.get("/widgets/beach_status?lat=43.5&lng=39.7&theme=light")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    text = r.text
    assert "TideGuard" in text
    assert "Cache-Control" in r.headers
    assert "Powered by" in text


@pytest.mark.asyncio
async def test_qr_endpoint_returns_png(client):
    r = await client.get("/widgets/beach_status/qr?lat=43.5&lng=39.7")
    if r.status_code == 503:
        pytest.skip("qrcode SDK is not installed")
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

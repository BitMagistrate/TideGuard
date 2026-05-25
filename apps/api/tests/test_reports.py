"""Tests for citizen report endpoints."""

from __future__ import annotations

import io

import pytest


@pytest.mark.asyncio
async def test_create_and_list_report(client, tmp_path, monkeypatch):
    # Stub photo upload to local
    monkeypatch.chdir(tmp_path)

    photo_bytes = b"fake-jpg-bytes"
    files = {"photo": ("trash.jpg", io.BytesIO(photo_bytes), "image/jpeg")}
    data = {
        "lat": "24.5",
        "lng": "120.5",
        "severity": "3",
        "debris_type": "plastic_bottle",
    }

    r = await client.post("/reports", data=data, files=files)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["xp"] >= 10
    assert "photo_url" in payload

    # List returns 0 because new reports start with status=pending
    r = await client.get("/reports", params={"bbox": "119,23,123,26"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_report_validation(client):
    files = {"photo": ("x.jpg", io.BytesIO(b"x"), "image/jpeg")}
    bad = {"lat": "999", "lng": "0", "severity": "3", "debris_type": "plastic_bottle"}
    r = await client.post("/reports", data=bad, files=files)
    assert r.status_code == 400

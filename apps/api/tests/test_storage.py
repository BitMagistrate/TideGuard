"""Tests for the photo upload service (MIME + size validation, EXIF strip)."""

from __future__ import annotations

import io

import pytest


@pytest.mark.asyncio
async def test_reject_unsupported_mime(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    files = {"photo": ("a.txt", io.BytesIO(b"not-an-image"), "text/plain")}
    data = {"lat": "24.0", "lng": "120.5", "severity": "2", "debris_type": "plastic_bottle"}
    r = await client.post("/reports", data=data, files=files)
    assert r.status_code == 415, r.text


@pytest.mark.asyncio
async def test_reject_too_large(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # 11 MB — over the 10 MB default cap
    big = io.BytesIO(b"\x00" * (11 * 1024 * 1024))
    files = {"photo": ("big.jpg", big, "image/jpeg")}
    data = {"lat": "24.0", "lng": "120.5", "severity": "2", "debris_type": "plastic_bottle"}
    r = await client.post("/reports", data=data, files=files)
    assert r.status_code == 413, r.text

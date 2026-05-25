"""GDPR Article 17 — right to erasure — covered by DELETE /reports/mine."""

from __future__ import annotations

import io

import pytest


def _png_1x1() -> bytes:
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000D49444154789C636000000200010002B9F5180100000049454E44AE426082"
    )


@pytest.mark.asyncio
async def test_delete_my_reports(client):
    files = {"photo": ("p.png", io.BytesIO(_png_1x1()), "image/png")}
    data = {"lat": "24.0", "lng": "120.5", "severity": "2", "debris_type": "plastic_bottle"}
    r = await client.post("/reports", data=data, files=files)
    assert r.status_code == 200

    r2 = await client.delete("/reports/mine")
    assert r2.status_code == 200, r2.text
    assert r2.json()["deleted"] >= 1

    r3 = await client.get("/reports/mine")
    assert r3.status_code == 200
    assert r3.json() == []

"""Tests for the usage-meter quota helper."""

from __future__ import annotations

import pytest

from tideguard_api.services.usage_meter import UsageMeter, rate_limit_headers


@pytest.mark.asyncio
async def test_quota_increments_and_blocks():
    meter = UsageMeter(namespace="tg:test")
    await meter.reset_for_tests()
    ok, _info = await meter.check_quota("acct-1", "free")
    assert ok is True

    # bump count up to the monthly quota for free tier (1000)
    for _ in range(1000):
        await meter.increment("acct-1")
    ok, info = await meter.check_quota("acct-1", "free")
    assert ok is False
    assert info["reason"] == "monthly_quota"


@pytest.mark.asyncio
async def test_rate_limit_headers_remaining():
    meter = UsageMeter(namespace="tg:hdr")
    await meter.reset_for_tests()
    await meter.increment("acct-h")
    cur = await meter.current("acct-h")
    hdrs = rate_limit_headers(cur, "free")
    assert hdrs["X-Rate-Limit-Tier"] == "free"
    assert int(hdrs["X-Rate-Limit-Remaining"]) == 999
    assert hdrs["X-Rate-Limit-Limit"] == "1000"


@pytest.mark.asyncio
async def test_enterprise_unlimited():
    meter = UsageMeter(namespace="tg:ent")
    await meter.reset_for_tests()
    for _ in range(2000):
        await meter.increment("ent-1")
    ok, info = await meter.check_quota("ent-1", "enterprise")
    assert ok is True
    cur = await meter.current("ent-1")
    hdrs = rate_limit_headers(cur, "enterprise")
    assert hdrs["X-Rate-Limit-Remaining"] == "unlimited"

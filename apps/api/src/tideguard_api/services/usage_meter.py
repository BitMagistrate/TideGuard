"""Per-key usage counter — Redis if available, in-memory fallback.

The plan (§2.5) wants per-minute / per-month counters keyed by the API key id
with a graceful degrade path when Redis is unavailable. We expose a small
helper class so callers don't care which backend is in use.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from tideguard_api.services.feature_gate import get_tier

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _Window:
    count: int = 0
    reset_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(seconds=60))


_MINUTE_COUNTERS: dict[str, _Window] = defaultdict(_Window)
_MONTH_COUNTERS: dict[str, int] = defaultdict(int)
_LOCK = asyncio.Lock()


class UsageMeter:
    """In-memory fallback that mirrors the Redis API.

    For production with Redis, swap the underlying dict with ``aioredis``
    calls; the surface area is intentionally minimal.
    """

    def __init__(self, namespace: str = "tg:usage") -> None:
        self.ns = namespace

    def _month_key(self, rate_key: str) -> str:
        ym = datetime.now(UTC).strftime("%Y-%m")
        return f"{self.ns}:{rate_key}:{ym}"

    def _minute_key(self, rate_key: str) -> str:
        return f"{self.ns}:{rate_key}:rps"

    async def increment(self, rate_key: str, n: int = 1) -> None:
        async with _LOCK:
            _MONTH_COUNTERS[self._month_key(rate_key)] += n
            w = _MINUTE_COUNTERS[self._minute_key(rate_key)]
            now = datetime.now(UTC)
            if now >= w.reset_at:
                w.count = 0
                w.reset_at = now + timedelta(seconds=60)
            w.count += n

    async def current(self, rate_key: str) -> dict[str, Any]:
        async with _LOCK:
            return {
                "month_count": _MONTH_COUNTERS.get(self._month_key(rate_key), 0),
                "rps_count": _MINUTE_COUNTERS.get(self._minute_key(rate_key), _Window()).count,
                "rps_reset_at": _MINUTE_COUNTERS.get(
                    self._minute_key(rate_key), _Window()
                ).reset_at.isoformat(),
            }

    async def check_quota(self, rate_key: str, tier_slug: str) -> tuple[bool, dict[str, Any]]:
        cur = await self.current(rate_key)
        tier = get_tier(tier_slug)
        month_quota = tier.get("monthly_quota")
        rps = tier.get("rps")
        if month_quota is not None and cur["month_count"] >= month_quota:
            return False, {"reason": "monthly_quota", **cur, "quota": month_quota}
        if rps is not None and cur["rps_count"] >= rps * 60:
            # rps×60 ≈ "per-minute" envelope for the in-mem fallback
            return False, {"reason": "rps", **cur, "rps_limit_per_min": rps * 60}
        return True, {**cur, "quota": month_quota, "rps_limit": rps}

    async def reset_for_tests(self) -> None:
        async with _LOCK:
            _MONTH_COUNTERS.clear()
            _MINUTE_COUNTERS.clear()


_DEFAULT_METER: UsageMeter | None = None


def get_meter() -> UsageMeter:
    global _DEFAULT_METER
    if _DEFAULT_METER is None:
        _DEFAULT_METER = UsageMeter(namespace=os.environ.get("API_KEY_REDIS_NAMESPACE", "tg:usage"))
    return _DEFAULT_METER


def rate_limit_headers(cur: dict[str, Any], tier_slug: str) -> dict[str, str]:
    tier = get_tier(tier_slug)
    quota = tier.get("monthly_quota")
    remaining = "unlimited"
    if quota is not None:
        remaining = str(max(quota - int(cur.get("month_count", 0)), 0))
    return {
        "X-Rate-Limit-Tier": tier_slug,
        "X-Rate-Limit-Limit": str(quota) if quota is not None else "unlimited",
        "X-Rate-Limit-Remaining": remaining,
        "X-Rate-Limit-Reset": cur.get("rps_reset_at", ""),
    }

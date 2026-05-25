"""Redis-or-memory cache for forecast/exceedance grids (TASK-014).

Avoids the bugs in CRIT-ML-10: float-keyed `lru_cache`, no TTL, and a seed
based on `datetime.now()` that goes stale after midnight.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

from tideguard_api.settings import get_settings

logger = logging.getLogger(__name__)


def _key(parts: tuple) -> str:
    rounded = tuple(round(x, 3) if isinstance(x, float) else x for x in parts)
    return "forecast:v2:" + "|".join(str(x) for x in rounded)


class _InProcessCache:
    """Thread-safe TTL cache, used when Redis is unreachable."""

    def __init__(self, maxsize: int = 1024) -> None:
        self._lock = threading.RLock()
        self._items: dict[str, tuple[float, Any]] = {}
        self._maxsize = maxsize

    def get(self, key: str) -> Any | None:
        with self._lock:
            row = self._items.get(key)
            if row is None:
                return None
            expires, value = row
            if expires < time.time():
                self._items.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            if len(self._items) >= self._maxsize:
                # Evict oldest 10% — coarse, fine for cache, not eviction-perfect.
                drop = max(1, self._maxsize // 10)
                for k in list(self._items.keys())[:drop]:
                    self._items.pop(k, None)
            self._items[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_local_cache = _InProcessCache()


def cached_or_compute(parts: tuple, compute: Callable[[], Any], ttl: int | None = None) -> Any:
    """Synchronous cache wrapper used by the tile renderer."""
    settings = get_settings()
    if ttl is None:
        ttl = settings.forecast_cache_ttl_seconds
    key = _key(parts)
    cached = _local_cache.get(key)
    if cached is not None:
        return cached
    value = compute()
    _local_cache.set(key, value, ttl)
    return value


async def async_cached_or_compute(parts: tuple, compute, ttl: int | None = None) -> Any:
    """Async variant — `compute` may be sync or a coroutine."""
    settings = get_settings()
    if ttl is None:
        ttl = settings.forecast_cache_ttl_seconds
    key = _key(parts)
    cached = _local_cache.get(key)
    if cached is not None:
        return cached
    result = compute()
    if asyncio.iscoroutine(result):
        result = await result
    _local_cache.set(key, result, ttl)
    return result


def clear_cache() -> None:
    _local_cache.clear()

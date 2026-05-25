"""Observability helpers — Prometheus metrics + OpenTelemetry hook.

Implements TASK-016 from TIDEGUARD_AUDIT.md. Metric registration and the
ASGI wrapper are no-ops when ``prometheus_client`` is not installed so that
the API keeps booting on minimal environments.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

try:  # pragma: no cover — optional dep
    from prometheus_client import Counter, Gauge, Histogram, generate_latest
    from prometheus_client.exposition import CONTENT_TYPE_LATEST

    _PROM_AVAILABLE = True
except Exception:  # noqa: BLE001
    _PROM_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain"

if _PROM_AVAILABLE:
    FORECAST_LATENCY = Histogram(
        "tideguard_forecast_latency_seconds",
        "Latency of /forecast inference in seconds.",
        ("source",),  # "pinn" | "mock" | "ensemble"
    )
    REPORT_UPLOADS = Counter(
        "tideguard_report_uploads_total",
        "Citizen reports submitted.",
        ("mime", "result"),
    )
    MODEL_LOADED = Gauge(
        "tideguard_model_loaded",
        "1 when the PINN checkpoint is loaded into memory.",
    )
    EXCEEDANCE_DURATION = Histogram(
        "tideguard_exceedance_latency_seconds",
        "Latency of /forecast/exceedance in seconds.",
    )
else:  # pragma: no cover — degenerate noop API
    class _NoOp:
        def labels(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return self

        def observe(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return None

        def inc(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return None

        def set(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return None

    FORECAST_LATENCY = _NoOp()  # type: ignore[assignment]
    REPORT_UPLOADS = _NoOp()  # type: ignore[assignment]
    MODEL_LOADED = _NoOp()  # type: ignore[assignment]
    EXCEEDANCE_DURATION = _NoOp()  # type: ignore[assignment]


def record_forecast(source: str) -> TimerCM:
    return TimerCM(FORECAST_LATENCY.labels(source=source))


def record_exceedance() -> TimerCM:
    return TimerCM(EXCEEDANCE_DURATION)


def record_upload(mime: str, result: str) -> None:
    REPORT_UPLOADS.labels(mime=mime or "unknown", result=result).inc()


def set_model_loaded(loaded: bool) -> None:
    MODEL_LOADED.set(1 if loaded else 0)


class TimerCM:
    def __init__(self, hist) -> None:  # type: ignore[no-untyped-def]
        self._hist = hist
        self._t0 = 0.0

    def __enter__(self) -> TimerCM:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *_exc) -> None:  # type: ignore[no-untyped-def]
        elapsed = time.perf_counter() - self._t0
        try:
            self._hist.observe(elapsed)
        except Exception:  # noqa: BLE001
            pass


def metrics_payload() -> tuple[bytes, str]:
    if not _PROM_AVAILABLE:
        return b"# prometheus_client not installed\n", "text/plain"
    return generate_latest(), CONTENT_TYPE_LATEST


def instrument_app(app: Any) -> None:
    """Best-effort OpenTelemetry instrumentation."""
    try:  # pragma: no cover — optional dep
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:  # noqa: BLE001
        logger.info("OpenTelemetry FastAPI instrumentation not available: %s", exc)


__all__ = [
    "FORECAST_LATENCY",
    "REPORT_UPLOADS",
    "MODEL_LOADED",
    "EXCEEDANCE_DURATION",
    "record_forecast",
    "record_exceedance",
    "record_upload",
    "set_model_loaded",
    "metrics_payload",
    "instrument_app",
]

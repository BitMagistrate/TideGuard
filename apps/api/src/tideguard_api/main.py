"""FastAPI application entry point.

Hardened per TIDEGUARD_AUDIT.md (TASK-005, TASK-006, TASK-016, CRIT-API-1..16):
  * Startup config guard for production (`Settings.validate_for_environment`).
  * MaxBodySizeMiddleware enforces a hard request body cap before parsing.
  * Slowapi keyed on the upstream proxy IP (not the LB IP).
  * CORS supports a regex pattern for preview deployments.
  * StaticFiles mount for the local upload fallback (so /uploads/photos/* works).
  * Prometheus /metrics endpoint when prometheus_client is installed.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from tideguard_api.db import Base, engine
from tideguard_api.middleware import (
    MaxBodySizeMiddleware,
    RequestIdMiddleware,
    proxied_key_func,
)
from tideguard_api.middleware_tier import TierEnforcementMiddleware
from tideguard_api.observability import instrument_app, metrics_payload
from tideguard_api.routers import (
    admin,
    adopt,
    api_keys,
    auth,
    b2g,
    b2g_dashboard,
    badges,
    billing,
    cleanup_planner,
    cleanups,
    cleanups_plan,
    developers,
    education,
    esg,
    forecast,
    impact,
    leaderboard,
    notifications,
    ogc,
    organizations,
    reports,
    routing_vrp,
    sustainability,
    tasking,
    tiles,
    widgets,
)
from tideguard_api.settings import get_settings


def _setup_logging(settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    if settings.log_json:
        fmt = '{"ts":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s %(levelname)s %(name)s — %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def _maybe_init_sentry(settings) -> None:
    if not settings.sentry_dsn:
        return
    try:  # pragma: no cover — optional dep
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.05 if settings.env == "production" else 0.2,
            send_default_pii=False,
        )
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning("Sentry init failed: %s", exc)


async def _auto_seed_if_requested(settings) -> None:
    """Run idempotent demo seeders on startup when ``AUTO_SEED_ON_STARTUP=1``.

    Best-effort: each seeder is wrapped in try/except so a partial failure
    does not block the API from coming up. Each script is itself idempotent.
    """
    if not settings.auto_seed_on_startup:
        return
    log = logging.getLogger(__name__)
    from tideguard_api.scripts import (
        seed_beach_segments,
        seed_lessons,
        seed_regions,
        seed_tiers,
    )

    for name, fn in [
        ("regions", seed_regions.main),
        ("beach_segments", seed_beach_segments.main),
        ("tiers", seed_tiers.main),
        ("lessons", seed_lessons.main),
    ]:
        try:
            await fn()
            log.info("auto-seed: %s ok", name)
        except Exception as exc:  # noqa: BLE001
            log.warning("auto-seed: %s failed: %s", name, exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()  # raises if prod misconfigured
    _setup_logging(settings)
    _maybe_init_sentry(settings)
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await _auto_seed_if_requested(settings)
    yield


# Slowapi limiter — proxy-aware (Fly / Cloudflare).
limiter = Limiter(key_func=proxied_key_func)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TideGuard API",
        description="Backend API for TideGuard AI — marine debris forecasting + community cleanup.",
        version="0.5.0",
        lifespan=lifespan,
    )

    # Merge ``EXTRA_CORS_ORIGINS`` (comma-separated env var) into the static
    # allow-list. Lets you whitelist the actual Vercel/Netlify URL handed to
    # the frontend without recompiling.
    extra = [o.strip().rstrip("/") for o in settings.extra_cors_origins.split(",") if o.strip()]
    effective_origins = list(dict.fromkeys([*settings.cors_origins, *extra]))
    allow_credentials = bool(effective_origins) and "*" not in effective_origins
    cors_kwargs: dict = dict(
        allow_origins=effective_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # CRIT-API-5 — hard body-size limit before multipart parsing.
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.request_max_body_bytes)

    # P1-13 — stamp every request with X-Request-Id for trace correlation.
    app.add_middleware(RequestIdMiddleware)

    # v0.5 — tier-enforcement / quota / rate-limit headers (no-op when
    # ``api_key_enforcement`` is false and no ``X-API-Key`` header is sent).
    app.add_middleware(TierEnforcementMiddleware)

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_request: Request, _exc: RateLimitExceeded):
        return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict:
        from tideguard_api.observability import _PROM_AVAILABLE  # type: ignore

        return {
            "status": "ok",
            "service": "tideguard-api",
            "version": "0.4.0",
            "env": settings.env,
            "domain": settings.domain_name,
            "metrics": settings.metrics_enabled and _PROM_AVAILABLE,
        }

    @app.get("/", tags=["health"])
    def root() -> dict:
        return {"name": "TideGuard API", "docs": "/docs", "health": "/healthz"}

    if settings.metrics_enabled:
        @app.get("/metrics", tags=["health"])
        def metrics() -> Response:
            body, ct = metrics_payload()
            return Response(content=body, media_type=ct)

    # CRIT-API-8 — local upload fallback must be reachable on /uploads/photos/*.
    uploads_dir = Path("uploads") / "photos"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    app.include_router(auth.router)
    app.include_router(forecast.router)
    app.include_router(reports.router)
    app.include_router(cleanups.router)
    app.include_router(cleanups_plan.router)
    app.include_router(education.router)
    app.include_router(leaderboard.router)
    app.include_router(tiles.router)
    app.include_router(badges.router)
    app.include_router(admin.router)
    app.include_router(b2g.router)
    app.include_router(impact.router)
    app.include_router(tasking.router)
    app.include_router(cleanup_planner.router)
    app.include_router(ogc.router)
    app.include_router(sustainability.router)
    app.include_router(developers.router)
    # v0.5 monetisation routers
    app.include_router(organizations.router)
    app.include_router(api_keys.router)
    app.include_router(billing.router)
    app.include_router(b2g_dashboard.router)
    app.include_router(routing_vrp.router)
    app.include_router(esg.router)
    app.include_router(widgets.router)
    app.include_router(adopt.router)
    app.include_router(notifications.router)

    @app.exception_handler(ValueError)
    async def value_error_handler(_request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    instrument_app(app)
    return app


app = create_app()

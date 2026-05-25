"""TierEnforcementMiddleware (§3.2.1.5).

Reads ``X-API-Key`` if present and routes the request through
``feature_gate.check_access`` + ``usage_meter.check_quota``.  When
``settings.api_key_enforcement`` is false (the default for v0.5
public-beta) the middleware adds rate-limit headers but does NOT
reject requests — this keeps the existing demo green while letting
operators flip enforcement on with a single env-var.
"""

from __future__ import annotations

import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from tideguard_api.db import SessionLocal
from tideguard_api.services.api_key_auth import resolve_caller
from tideguard_api.services.feature_gate import check_access, normalise_endpoint
from tideguard_api.services.usage_meter import get_meter, rate_limit_headers
from tideguard_api.settings import get_settings

logger = logging.getLogger(__name__)


_EXEMPT_PREFIXES = (
    "/healthz",
    "/metrics",
    "/billing/webhook/",
    "/auth/",
    "/api_keys",
    "/orgs",
    "/developers",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/uploads",
)


def _is_exempt(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in _EXEMPT_PREFIXES)


class TierEnforcementMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        req = Request(scope, receive=receive)
        path = req.url.path

        # Always exempt list — no resolver work.
        if _is_exempt(path):
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        api_key_header = req.headers.get("x-api-key") or req.headers.get("X-API-Key")

        # If no key is provided AND enforcement is off, skip — keeps v0.4 endpoints public.
        if not api_key_header and not settings.api_key_enforcement:
            await self.app(scope, receive, send)
            return

        async with SessionLocal() as db:
            caller = await resolve_caller(req, db)

        if caller.tier == "invalid_key":
            await self._respond(scope, receive, send, JSONResponse({"detail": "invalid API key"}, status_code=401))
            return

        decision = check_access(caller.tier, normalise_endpoint(path), dict(req.query_params))
        if not decision.allow:
            status = 402 if decision.reason == "tier_too_low" else 403
            payload = {
                "detail": "tier_too_low" if status == 402 else decision.reason,
                "tier": caller.tier,
                "endpoint": path,
                "upgrade_url": "/pricing",
            }
            await self._respond(scope, receive, send, JSONResponse(payload, status_code=status))
            return

        meter = get_meter()
        ok, info = await meter.check_quota(caller.rate_key, caller.tier)
        if not ok:
            await self._respond(
                scope, receive, send,
                JSONResponse(
                    {"detail": "quota_exceeded", **info, "upgrade_url": "/pricing"},
                    status_code=429,
                    headers={"X-Rate-Limit-Tier": caller.tier},
                ),
            )
            return

        # Patch send so we can append rate-limit headers + record usage on response start.
        async def send_with_headers(event):
            if event["type"] == "http.response.start":
                cur = await meter.current(caller.rate_key)
                hdrs = rate_limit_headers(cur, caller.tier)
                if decision.requires_attribution:
                    hdrs["X-Attribution-Required"] = "true"
                headers = list(event.get("headers", []))
                for k, v in hdrs.items():
                    headers.append((k.encode("latin-1"), v.encode("latin-1")))
                event["headers"] = headers
            await send(event)

        await meter.increment(caller.rate_key)
        await self.app(scope, receive, send_with_headers)

    async def _respond(self, scope, receive, send, response: Response) -> None:
        await response(scope, receive, send)

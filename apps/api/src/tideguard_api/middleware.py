"""Custom ASGI middleware for TideGuard.

Implemented per audit TASK-006 / CRIT-API-5: a hard request-body limit
applied *before* multipart parsing so that we never pull a 5 GB upload into
RAM, and CRIT-API-12: a slowapi key function that respects upstream proxies.

P1-13 adds an X-Request-Id middleware that stamps a UUIDv4 onto every
request (using the inbound header value when present) and attaches it
to the structured log context.
"""

from __future__ import annotations

import contextvars
import logging
import uuid

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tideguard_request_id", default=""
)


def get_request_id() -> str:
    """Return the current request id, or '' if outside a request."""
    return _request_id_var.get()


class RequestIdMiddleware:
    """Stamp an ``X-Request-Id`` header on every response.

    The middleware honours an inbound ``X-Request-Id`` header (so
    upstream proxies can correlate requests across services) and falls
    back to a fresh UUIDv4 otherwise.  The id is also pushed onto a
    ``ContextVar`` so structlog can include it in the JSON log entry
    via ``structlog.contextvars.bind_contextvars``.
    """

    def __init__(self, app: ASGIApp, header: str = "x-request-id") -> None:
        self.app = app
        self.header = header.lower()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming = None
        for name, value in scope.get("headers", []) or []:
            if name == self.header.encode("latin-1"):
                incoming = value.decode("latin-1")
                break
        request_id = incoming or uuid.uuid4().hex
        token = _request_id_var.set(request_id)

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []) or [])
                headers.append((self.header.encode("latin-1"), request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            _request_id_var.reset(token)


class MaxBodySizeMiddleware:
    """Reject HTTP requests whose body exceeds ``max_bytes`` before parsing."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Enforce a declared Content-Length if present — cheaper than reading.
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value.decode("latin-1"))
                except ValueError:
                    declared = 0
                if declared > self.max_bytes:
                    await self._reject(send)
                    return

        received = 0
        client_disconnected = False

        async def wrapped_receive() -> Message:
            nonlocal received, client_disconnected
            msg = await receive()
            mtype = msg.get("type")
            if mtype == "http.disconnect":
                client_disconnected = True
                return msg
            if mtype == "http.request":
                received += len(msg.get("body", b"") or b"")
                if received > self.max_bytes:
                    # Drain remaining body bytes silently; downstream sees a 413.
                    # We must NOT loop forever if the client has already
                    # disconnected — treat ``http.disconnect`` as a terminal
                    # message (B11).
                    if msg.get("more_body"):
                        try:
                            while True:
                                more = await receive()
                                more_type = more.get("type")
                                if more_type == "http.disconnect":
                                    client_disconnected = True
                                    break
                                if more_type != "http.request":
                                    break
                                if not more.get("more_body"):
                                    break
                        except Exception:  # noqa: BLE001
                            pass
                    raise _BodyTooLarge(self.max_bytes)
            return msg

        try:
            await self.app(scope, wrapped_receive, send)
        except _BodyTooLarge as exc:
            logger.info("Rejected oversized request body (limit=%d)", exc.limit)
            if client_disconnected:
                # Client already gave up — nothing to send.
                return
            await self._reject(send)

    async def _reject(self, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large (limit {self.max_bytes} bytes)"},
        )
        async def _empty_receive() -> dict[str, object]:
            return {"type": "http.disconnect"}

        await response({"type": "http"}, _empty_receive, send)  # type: ignore[arg-type]
        return None


class _BodyTooLarge(Exception):
    def __init__(self, limit: int) -> None:
        super().__init__(f"body > {limit}")
        self.limit = limit


def proxied_key_func(request) -> str:  # type: ignore[no-untyped-def]
    """SlowAPI key function that respects Fly / Cloudflare / X-Forwarded-For.

    Per CRIT-API-12, the default `get_remote_address` returns the LB IP behind
    Fly.io, defeating per-IP rate limiting. We prefer the upstream proxy's
    `Fly-Client-IP` / `CF-Connecting-IP` / `X-Real-IP` / `X-Forwarded-For`
    headers (first value, comma-split), and fall back to `request.client.host`.
    """
    headers = request.headers
    for name in ("fly-client-ip", "cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        value = headers.get(name)
        if value:
            return str(value.split(",", 1)[0].strip())
    client = request.client
    return client.host if client else "anonymous"

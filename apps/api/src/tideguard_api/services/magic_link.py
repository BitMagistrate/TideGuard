"""Magic-link / passwordless email login helper (§2.7)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from tideguard_api.settings import get_settings


def issue_magic_token(email: str, name: str | None = None, ttl_seconds: int | None = None) -> str:
    settings = get_settings()
    ttl = ttl_seconds or settings.magic_link_ttl_seconds
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid5(uuid.NAMESPACE_DNS, email)),
        "email": email,
        "name": name or email.split("@")[0],
        "iss": settings.jwt_issuer,
        "aud": "tideguard-magic-link",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        "kind": "magic-link",
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_magic_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="tideguard-magic-link",
            issuer=settings.jwt_issuer,
        )
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc
    if payload.get("kind") != "magic-link":
        raise ValueError("not a magic-link token")
    return dict(payload)


def build_verify_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/auth/verify?token={token}"

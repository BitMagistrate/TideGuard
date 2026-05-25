"""API-key generation, hashing and lookup helpers.

Format: ``<prefix>_<base32-secret>`` (prefix is ``tg_live`` / ``tg_test``).
We only ever store ``sha256(secret)`` — the plain-text is shown to the
user exactly once at creation time. Lookup is constant-time on the
already-hashed value, matching the audit checklist in §9.3.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.models.api_key import ApiKey
from tideguard_api.models.subscription import Subscription
from tideguard_api.models.tier import Tier

DEFAULT_PREFIX = "tg_live"
TEST_PREFIX = "tg_test"
_SECRET_BYTES = 18  # 18 raw bytes → 29 base32 chars → key fits in 40 chars total


@dataclass(slots=True)
class Caller:
    """The resolved caller — either an authenticated API key or a fallback."""

    kind: str  # "api_key" | "anonymous" | "jwt"
    tier: str
    org_id: uuid.UUID | None = None
    api_key_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    rate_key: str = "anonymous"


def generate_api_key(prefix: str = DEFAULT_PREFIX) -> tuple[str, str, str]:
    """Return ``(full_key, last4, sha256_hex)``.

    Only the hash is stored. The plaintext must be shown to the user
    exactly once at creation time.
    """
    raw = secrets.token_bytes(_SECRET_BYTES)
    body = base64.b32encode(raw).decode("ascii").rstrip("=").lower()
    full = f"{prefix}_{body}"
    last4 = full[-4:]
    hsh = hash_key(full)
    return full, last4, hsh


def hash_key(key: str) -> str:
    """SHA-256 hex of the full key (constant-time compatible)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


async def lookup_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    """Find an active API-key row matching ``raw_key`` (constant-time)."""
    if not raw_key or "_" not in raw_key:
        return None
    candidate_hash = hash_key(raw_key)
    res = await db.execute(select(ApiKey).where(ApiKey.hash == candidate_hash))
    row = res.scalar_one_or_none()
    if row is None or row.status != "active":
        return None
    if row.expires_at and row.expires_at < datetime.now(UTC):
        return None
    return row


async def resolve_caller(request: Request, db: AsyncSession) -> Caller:
    """FastAPI dependency: extract caller identity from headers.

    Order of precedence:
      1. ``X-API-Key`` (live key).
      2. ``Authorization: Bearer …`` (handled separately by ``get_current_user``;
         here we surface a ``jwt`` placeholder tier — middleware will trust JWT
         only for billing/api_keys endpoints).
      3. Anonymous → free tier, rate-limited by IP.
    """
    header_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if header_key:
        row = await lookup_api_key(db, header_key)
        if row is not None:
            # Resolve tier via active subscription, fall back to "free".
            tier_slug = "free"
            sub_res = await db.execute(
                select(Subscription).where(
                    Subscription.org_id == row.org_id,
                    Subscription.status.in_(("trial", "active", "past_due")),
                )
            )
            sub = sub_res.scalars().first()
            if sub is not None:
                t = await db.execute(select(Tier).where(Tier.id == sub.tier_id))
                tier_row = t.scalar_one_or_none()
                if tier_row is not None:
                    tier_slug = tier_row.slug
            return Caller(
                kind="api_key",
                tier=tier_slug,
                org_id=row.org_id,
                api_key_id=row.id,
                rate_key=str(row.id),
            )
        # Bad key → 401 (raised by caller)
        return Caller(kind="anonymous", tier="invalid_key", rate_key="invalid")

    # No explicit key → anonymous (free).
    client_ip = "anonymous"
    if request.client is not None:
        client_ip = request.client.host
    return Caller(kind="anonymous", tier="free", rate_key=f"ip:{client_ip}")


def env_for_prefix() -> str:
    return TEST_PREFIX if os.environ.get("TIDEGUARD_API_KEY_ENV", "live") == "test" else DEFAULT_PREFIX

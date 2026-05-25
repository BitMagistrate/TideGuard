"""Auth endpoints — `/me`, `/auth/dev_token`.

Per audit CRIT-API-3 the dev-token endpoint is now also blocked in
``staging`` and ``production`` environments regardless of the
``allow_anonymous_dev_user`` flag — only ``development`` / ``test`` may use it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.user import User
from tideguard_api.schemas.billing import MagicLinkRequest, MagicLinkResponse
from tideguard_api.services.email_sender import EmailMessage, get_email_sender
from tideguard_api.services.magic_link import (
    issue_magic_token,
    verify_magic_token,
)
from tideguard_api.settings import get_settings

router = APIRouter(tags=["auth"])


class DevTokenRequest(BaseModel):
    email: EmailStr
    name: str | None = None


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    expires_in: int


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "xp": user.xp,
        "school_id": str(user.school_id) if user.school_id else None,
    }


@router.post("/auth/dev_token", response_model=DevTokenResponse)
async def issue_dev_token(
    payload: DevTokenRequest, db: AsyncSession = Depends(get_db)
) -> DevTokenResponse:
    """Issue a short-lived JWT for the given email.

    Only available in ``development`` / ``test`` environments. The
    audit (CRIT-API-3) explicitly called this out as a privilege-escalation
    vector when shipped to prod.
    """
    settings = get_settings()
    if settings.env not in ("development", "test"):
        raise HTTPException(403, "Dev token endpoint disabled in this environment")
    if not settings.allow_anonymous_dev_user:
        raise HTTPException(403, "Dev token endpoint disabled in this environment")

    existing = await db.execute(select(User).where(User.email == payload.email))
    user = existing.scalar_one_or_none()
    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=str(payload.email),
            name=payload.name or str(payload.email).split("@")[0],
            role="user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    now = datetime.now(UTC)
    exp = now + timedelta(seconds=settings.jwt_ttl_seconds)
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return DevTokenResponse(
        access_token=token,
        user_id=str(user.id),
        expires_in=settings.jwt_ttl_seconds,
    )


# --- P1-14: OIDC + JWKS endpoints ---------------------------------------------


class OIDCStartResponse(BaseModel):
    authorize_url: str
    state: str


@router.get("/auth/oidc/start", response_model=OIDCStartResponse)
async def oidc_start() -> OIDCStartResponse:
    """Begin the OIDC authorisation-code flow.

    Returns the authorize URL the client must redirect the user to.
    The state parameter is a fresh UUIDv4 — the client must echo it
    back on the callback.
    """
    settings = get_settings()
    if not settings.oidc_client_id:
        raise HTTPException(503, "OIDC is not configured on this deployment")
    import urllib.parse

    state = uuid.uuid4().hex
    params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "scope": "openid email profile",
        "state": state,
    }
    base = settings.oidc_issuer.rstrip("/") + "/authorize"
    return OIDCStartResponse(
        authorize_url=f"{base}?{urllib.parse.urlencode(params)}",
        state=state,
    )


@router.get("/auth/jwks.json")
async def jwks() -> dict:
    """Return a minimal JWKS document advertising the API's HMAC key.

    For a HS256 deployment the JWKS only carries the ``kty`` and the
    ``kid``.  Asymmetric (RS256) deployments override ``jwt_secret``
    with a JWK and serve the public half here.
    """
    settings = get_settings()
    return {
        "keys": [
            {
                "kid": settings.jwt_kid,
                "kty": "oct",
                "alg": settings.jwt_algorithm,
                "use": "sig",
            }
        ]
    }


@router.get("/.well-known/openid-configuration")
async def oidc_discovery() -> dict:
    """OIDC discovery document — minimal but spec-compliant.

    Lets external clients (e.g. Auth0 federation) configure themselves
    against the API without manual coordination.
    """
    settings = get_settings()
    base = settings.jwt_issuer.rstrip("/")
    return {
        "issuer": base,
        "jwks_uri": f"{base}/auth/jwks.json",
        "authorization_endpoint": f"{settings.oidc_issuer.rstrip('/')}/authorize"
        if settings.oidc_issuer else None,
        "token_endpoint": f"{settings.oidc_issuer.rstrip('/')}/oauth/token"
        if settings.oidc_issuer else None,
        "id_token_signing_alg_values_supported": [settings.jwt_algorithm],
        "response_types_supported": ["code", "id_token", "token id_token"],
        "scopes_supported": ["openid", "email", "profile"],
        "subject_types_supported": ["public"],
    }


# --- v0.5: Magic-link / passwordless flow -----------------------------------


@router.post("/auth/magic_link", response_model=MagicLinkResponse)
async def request_magic_link(
    payload: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
) -> MagicLinkResponse:
    """Issue a one-time magic-link token and email it to the user."""
    settings = get_settings()
    token = issue_magic_token(str(payload.email), payload.name)
    callback = payload.callback_url or "https://app.tideguard.app/auth/verify"
    sender = get_email_sender()
    verify_url = f"{callback.rstrip('/')}?token={token}"
    try:
        sender.send(
            EmailMessage(
                to=str(payload.email),
                subject="Your TideGuard sign-in link",
                html=(
                    f"<p>Click the link below to sign in to TideGuard:</p>"
                    f'<p><a href="{verify_url}">{verify_url}</a></p>'
                    f"<p>Expires in {settings.magic_link_ttl_seconds // 60} minutes.</p>"
                ),
                text=f"Sign-in link: {verify_url}",
            )
        )
    except Exception:  # noqa: BLE001 — never fail the auth flow on email outage
        pass

    return MagicLinkResponse(
        sent=True,
        expires_in_seconds=settings.magic_link_ttl_seconds,
        debug_token=token if settings.env in ("development", "test") else None,
    )


class MagicVerifyRequest(BaseModel):
    token: str


@router.post("/auth/verify", response_model=DevTokenResponse)
async def verify_magic_link(
    payload: MagicVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> DevTokenResponse:
    """Exchange a magic-link token for an access JWT.

    Auto-provisions the user in the local database if they don't exist yet.
    """
    settings = get_settings()
    try:
        claims = verify_magic_token(payload.token)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc

    email = claims["email"]
    name = claims.get("name", email.split("@")[0])
    existing = await db.execute(select(User).where(User.email == email))
    user = existing.scalar_one_or_none()
    if user is None:
        user = User(id=uuid.uuid4(), email=email, name=name, role="user")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    now = datetime.now(UTC)
    exp = now + timedelta(seconds=settings.jwt_ttl_seconds)
    access_claims = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(access_claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return DevTokenResponse(
        access_token=token,
        user_id=str(user.id),
        expires_in=settings.jwt_ttl_seconds,
    )

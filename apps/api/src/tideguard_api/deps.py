"""FastAPI dependencies (auth + DB session)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.models.user import User
from tideguard_api.settings import get_settings

# Fixed UUID for the deterministic dev user so tests/dev work without auth.
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_USER_EMAIL = "dev@tideguard.app"


async def _get_or_create_dev_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == DEV_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=DEV_USER_ID,
            email=DEV_USER_EMAIL,
            name="Dev User",
            role="user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


def _decode_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    return dict(payload) if payload else {}


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from a Bearer JWT (HS256).

    Dev / test mode: when ``allow_anonymous_dev_user`` is true and no
    ``Authorization`` header is provided, a fixed deterministic dev user is
    returned (or created). In production set ``ALLOW_ANONYMOUS_DEV_USER=false``
    to disable this fallback.
    """
    settings = get_settings()

    if not authorization or not authorization.lower().startswith("bearer "):
        if settings.allow_anonymous_dev_user:
            return await _get_or_create_dev_user(db)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Empty bearer token")

    payload = _decode_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing subject")

    # `sub` is the user UUID; we look up the user. Issuing the dev_token endpoint
    # writes a User row first, so we never trust an unmatched UUID.
    try:
        user_uuid = uuid.UUID(sub)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token subject is not a UUID") from exc

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user


async def require_moderator(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "moderator"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Moderator only")
    return user

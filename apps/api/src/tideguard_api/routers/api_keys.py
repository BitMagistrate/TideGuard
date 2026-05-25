"""CRUD for API keys (§2.2)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.api_key import ApiKey
from tideguard_api.models.organization import Organization, OrgMember
from tideguard_api.models.user import User
from tideguard_api.schemas.billing import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyOut
from tideguard_api.services.api_key_auth import DEFAULT_PREFIX, generate_api_key

router = APIRouter(prefix="/api_keys", tags=["billing"])

_MAX_KEYS_PER_ORG = 10


async def _resolve_org(db: AsyncSession, user: User, org_slug: str | None) -> Organization:
    if org_slug is None:
        # Default: first org the user owns. Otherwise create a personal org.
        rows = await db.execute(
            select(Organization)
            .join(OrgMember, OrgMember.org_id == Organization.id)
            .where(OrgMember.user_id == user.id)
        )
        org = rows.scalars().first()
        if org is not None:
            return org
        org = Organization(
            id=uuid.uuid4(),
            slug=f"user-{str(user.id)[:8]}",
            name=user.name or user.email,
            owner_user_id=user.id,
            billing_email=user.email,
            billing_provider="stripe",
        )
        db.add(org)
        db.add(OrgMember(org_id=org.id, user_id=user.id, role="owner"))
        await db.commit()
        await db.refresh(org)
        return org
    res = await db.execute(select(Organization).where(Organization.slug == org_slug))
    org = res.scalar_one_or_none()
    if org is None:
        raise HTTPException(404, "org not found")
    mem = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org.id, OrgMember.user_id == user.id)
    )
    if mem.scalar_one_or_none() is None:
        raise HTTPException(403, "not a member of this org")
    return org


def _to_out(row: ApiKey) -> ApiKeyOut:
    return ApiKeyOut(
        id=str(row.id),
        name=row.name,
        prefix=row.prefix,
        last4=row.last4,
        scopes=row.scopes,
        status=row.status,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
    )


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiKeyCreatedResponse:
    org = await _resolve_org(db, user, payload.org_slug)

    active_rows = await db.execute(
        select(ApiKey).where(ApiKey.org_id == org.id, ApiKey.status == "active")
    )
    active_count = len(active_rows.scalars().all())
    if active_count >= _MAX_KEYS_PER_ORG:
        raise HTTPException(409, "max active api-keys reached for this organization")

    full, last4, hsh = generate_api_key(prefix=DEFAULT_PREFIX)
    row = ApiKey(
        id=uuid.uuid4(),
        org_id=org.id,
        created_by_user_id=user.id,
        name=payload.name,
        prefix=DEFAULT_PREFIX,
        hash=hsh,
        last4=last4,
        scopes=payload.scopes,
        status="active",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    out = _to_out(row).model_dump()
    return ApiKeyCreatedResponse(**out, plaintext=full)


@router.get("", response_model=list[ApiKeyOut])
async def list_keys(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ApiKeyOut]:
    rows = await db.execute(
        select(ApiKey)
        .join(OrgMember, OrgMember.org_id == ApiKey.org_id)
        .where(OrgMember.user_id == user.id, ApiKey.status != "revoked")
    )
    return [_to_out(r) for r in rows.scalars()]


@router.delete("/{key_id}", status_code=204)
async def revoke_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    res = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "api-key not found")
    mem = await db.execute(
        select(OrgMember).where(OrgMember.org_id == row.org_id, OrgMember.user_id == user.id)
    )
    if mem.scalar_one_or_none() is None:
        raise HTTPException(403, "cannot revoke a key from another org")
    row.status = "revoked"
    await db.commit()


@router.post("/{key_id}/rotate", response_model=ApiKeyCreatedResponse)
async def rotate_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiKeyCreatedResponse:
    res = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    old = res.scalar_one_or_none()
    if old is None:
        raise HTTPException(404, "api-key not found")
    mem = await db.execute(
        select(OrgMember).where(OrgMember.org_id == old.org_id, OrgMember.user_id == user.id)
    )
    if mem.scalar_one_or_none() is None:
        raise HTTPException(403, "cannot rotate a key from another org")

    full, last4, hsh = generate_api_key(prefix=old.prefix)
    new_row = ApiKey(
        id=uuid.uuid4(),
        org_id=old.org_id,
        created_by_user_id=user.id,
        name=old.name + " (rotated)",
        prefix=old.prefix,
        hash=hsh,
        last4=last4,
        scopes=old.scopes,
        status="active",
    )
    old.expires_at = datetime.now(UTC) + timedelta(days=7)
    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)
    out = _to_out(new_row).model_dump()
    return ApiKeyCreatedResponse(**out, plaintext=full)

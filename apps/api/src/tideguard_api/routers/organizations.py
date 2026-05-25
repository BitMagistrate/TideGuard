"""Organization management — create / list / invite members."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.organization import Organization, OrgMember
from tideguard_api.models.user import User
from tideguard_api.schemas.billing import OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/orgs", tags=["billing"])


def _to_out(org: Organization) -> OrganizationOut:
    return OrganizationOut(
        id=str(org.id),
        slug=org.slug,
        name=org.name,
        billing_email=org.billing_email,
        billing_provider=org.billing_provider,
        created_at=org.created_at,
    )


@router.post("", response_model=OrganizationOut, status_code=201)
async def create_org(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationOut:
    existing = await db.execute(select(Organization).where(Organization.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(409, "organization slug already in use")
    org = Organization(
        id=uuid.uuid4(),
        slug=payload.slug,
        name=payload.name,
        owner_user_id=user.id,
        billing_email=str(payload.billing_email) if payload.billing_email else user.email,
        billing_provider="stripe",
    )
    db.add(org)
    db.add(OrgMember(org_id=org.id, user_id=user.id, role="owner"))
    await db.commit()
    await db.refresh(org)
    return _to_out(org)


@router.get("", response_model=list[OrganizationOut])
async def list_orgs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrganizationOut]:
    rows = await db.execute(
        select(Organization).join(OrgMember, OrgMember.org_id == Organization.id).where(OrgMember.user_id == user.id)
    )
    return [_to_out(o) for o in rows.scalars()]


@router.get("/{slug}", response_model=OrganizationOut)
async def get_org(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationOut:
    res = await db.execute(select(Organization).where(Organization.slug == slug))
    org = res.scalar_one_or_none()
    if org is None:
        raise HTTPException(404, "organization not found")
    membership = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org.id, OrgMember.user_id == user.id)
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(403, "not a member of this organization")
    return _to_out(org)

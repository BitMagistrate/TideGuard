"""Billing endpoints (§2.3, §3.2.1).

Provides Stripe / Paddle / Manual checkout + portal + webhook intake. The
webhook handler is idempotent via the ``billing_events`` table.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.organization import Organization, OrgMember
from tideguard_api.models.subscription import BillingEvent, Subscription
from tideguard_api.models.tier import Tier
from tideguard_api.models.user import User
from tideguard_api.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalRequest,
    SubscriptionOut,
    WebhookResponse,
)
from tideguard_api.services.billing_gateway import get_billing_gateway

router = APIRouter(prefix="/billing", tags=["billing"])


async def _resolve_primary_org(db: AsyncSession, user: User) -> Organization | None:
    rows = await db.execute(
        select(Organization).join(OrgMember, OrgMember.org_id == Organization.id).where(OrgMember.user_id == user.id)
    )
    return rows.scalars().first()


async def _ensure_org(db: AsyncSession, user: User) -> Organization:
    org = await _resolve_primary_org(db, user)
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


async def _get_tier(db: AsyncSession, slug: str) -> Tier:
    res = await db.execute(select(Tier).where(Tier.slug == slug))
    tier = res.scalar_one_or_none()
    if tier is None:
        raise HTTPException(404, f"unknown tier slug {slug!r}")
    return tier


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckoutResponse:
    org = await _ensure_org(db, user)
    tier = await _get_tier(db, payload.tier_slug)
    gateway = get_billing_gateway()
    if not org.billing_customer_id:
        cid = gateway.create_customer(
            email=org.billing_email or user.email,
            name=org.name,
            metadata={"org_id": str(org.id)},
        )
        org.billing_customer_id = cid
        await db.commit()

    price_id = tier.stripe_price_id_yearly if payload.billing_period == "yearly" else tier.stripe_price_id_monthly
    price_id = price_id or f"price_{tier.slug}_{payload.billing_period}"
    url = gateway.create_checkout_session(
        customer_id=org.billing_customer_id,
        price_id=price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    return CheckoutResponse(url=url)


@router.post("/portal", response_model=CheckoutResponse)
async def create_portal(
    payload: PortalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckoutResponse:
    org = await _ensure_org(db, user)
    if not org.billing_customer_id:
        raise HTTPException(400, "no billing customer registered for this organisation")
    gateway = get_billing_gateway()
    url = gateway.create_portal_session(org.billing_customer_id, payload.return_url)
    return CheckoutResponse(url=url)


@router.post("/cancel", status_code=204)
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    org = await _ensure_org(db, user)
    res = await db.execute(
        select(Subscription).where(
            Subscription.org_id == org.id,
            Subscription.status.in_(("trial", "active", "past_due")),
        )
    )
    sub = res.scalars().first()
    if sub is None:
        raise HTTPException(404, "no active subscription")
    sub.cancel_at_period_end = True
    sub.status = "cancelled"
    await db.commit()


@router.get("/subscription", response_model=SubscriptionOut | None)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionOut | None:
    org = await _resolve_primary_org(db, user)
    if org is None:
        return None
    res = await db.execute(
        select(Subscription).where(
            Subscription.org_id == org.id,
            Subscription.status.in_(("trial", "active", "past_due")),
        ).order_by(Subscription.created_at.desc())
    )
    sub = res.scalars().first()
    if sub is None:
        return None
    tier_res = await db.execute(select(Tier).where(Tier.id == sub.tier_id))
    tier = tier_res.scalar_one_or_none()
    return SubscriptionOut(
        id=str(sub.id),
        org_id=str(sub.org_id),
        tier_slug=tier.slug if tier else "free",
        status=sub.status,
        provider=sub.provider,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
    )


@router.post("/webhook/{provider}", response_model=WebhookResponse)
async def webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    paddle_signature: str | None = Header(None, alias="Paddle-Signature"),
) -> WebhookResponse:
    payload = await request.body()
    signature = stripe_signature or paddle_signature or request.headers.get("x-signature", "")
    gateway = get_billing_gateway()
    if provider != gateway.provider_name and provider != "manual":
        raise HTTPException(400, f"webhook provider {provider!r} disabled")
    try:
        evt = gateway.parse_webhook(signature, payload)
    except ValueError as exc:
        raise HTTPException(401, f"invalid signature: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"webhook parse failed: {exc}") from exc

    # Idempotency
    existing = await db.execute(
        select(BillingEvent).where(
            BillingEvent.provider == evt.provider,
            BillingEvent.provider_event_id == evt.provider_event_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return WebhookResponse(received=True, event_id=evt.provider_event_id)

    await _apply_webhook(db, evt)
    db.add(
        BillingEvent(
            provider=evt.provider,
            provider_event_id=evt.provider_event_id,
            event_type=evt.event_type,
            payload=evt.payload,
        )
    )
    await db.commit()
    return WebhookResponse(received=True, event_id=evt.provider_event_id)


async def _apply_webhook(db: AsyncSession, evt) -> None:  # type: ignore[no-untyped-def]
    """Translate gateway events into ``subscriptions`` state changes."""
    payload = evt.payload or {}
    metadata = payload.get("metadata") or {}
    customer_id = payload.get("customer") or metadata.get("customer_id")
    tier_slug = metadata.get("tier_slug") or payload.get("tier_slug") or "pro"

    org = None
    if customer_id:
        res = await db.execute(select(Organization).where(Organization.billing_customer_id == customer_id))
        org = res.scalar_one_or_none()
    if org is None and metadata.get("org_id"):
        res = await db.execute(select(Organization).where(Organization.id == metadata["org_id"]))
        org = res.scalar_one_or_none()
    if org is None:
        # No matching org — record event but do nothing.
        return

    tier_res = await db.execute(select(Tier).where(Tier.slug == tier_slug))
    tier = tier_res.scalar_one_or_none()
    if tier is None:
        return

    if evt.event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "subscription.created",
        "subscription.updated",
        "invoice.payment_succeeded",
    ):
        sub_res = await db.execute(
            select(Subscription).where(Subscription.org_id == org.id, Subscription.tier_id == tier.id)
        )
        sub = sub_res.scalar_one_or_none()
        if sub is None:
            sub = Subscription(
                id=uuid.uuid4(),
                org_id=org.id,
                tier_id=tier.id,
                provider=evt.provider,
            )
            db.add(sub)
        sub.status = "active"
        sub.provider_subscription_id = payload.get("id") or sub.provider_subscription_id
        sub.current_period_start = datetime.now(UTC)
        sub.current_period_end = datetime.now(UTC) + timedelta(days=30)
        sub.cancel_at_period_end = False
    elif evt.event_type in ("customer.subscription.deleted", "subscription.cancelled"):
        sub_res = await db.execute(
            select(Subscription).where(Subscription.org_id == org.id, Subscription.tier_id == tier.id)
        )
        for sub in sub_res.scalars():
            sub.status = "cancelled"
            sub.cancel_at_period_end = True
    elif evt.event_type == "invoice.payment_failed":
        sub_res = await db.execute(
            select(Subscription).where(Subscription.org_id == org.id, Subscription.tier_id == tier.id)
        )
        for sub in sub_res.scalars():
            sub.status = "past_due"

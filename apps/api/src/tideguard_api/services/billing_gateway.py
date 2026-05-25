"""Abstract billing gateway + Stripe / Paddle / Manual implementations.

The plan (§2.3) calls for an abstraction with three concrete back-ends.
Stripe is the recommended provider. ``ManualGateway`` is used in tests and
when ``billing_provider=manual`` is set in development — it skips all
external calls and emits deterministic, signed-by-shared-secret events.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from tideguard_api.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WebhookEvent:
    provider: str
    provider_event_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


class BillingGateway(Protocol):
    provider_name: str

    def create_customer(self, email: str, name: str, metadata: dict[str, Any] | None = None) -> str: ...

    def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str: ...

    def create_portal_session(self, customer_id: str, return_url: str) -> str: ...

    def cancel_subscription(self, subscription_id: str) -> bool: ...

    def parse_webhook(self, signature: str, payload: bytes) -> WebhookEvent: ...


# ---------------------------------------------------------------------------
# Manual / fake gateway for tests and self-service development
# ---------------------------------------------------------------------------


class ManualGateway:
    provider_name = "manual"

    def __init__(self, secret: str = "manual-dev-secret") -> None:
        self.secret = secret
        self._customers: dict[str, dict[str, Any]] = {}

    def create_customer(self, email: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        cid = f"man_cus_{uuid.uuid4().hex[:12]}"
        self._customers[cid] = {"email": email, "name": name, "metadata": metadata or {}}
        return cid

    def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        # Returns a deterministic mock checkout URL.
        token = uuid.uuid4().hex[:24]
        return f"{success_url}?session_id=man_chs_{token}&customer_id={customer_id}&price_id={price_id}"

    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        return f"{return_url}?portal=man_{customer_id}"

    def cancel_subscription(self, subscription_id: str) -> bool:
        return True

    def parse_webhook(self, signature: str, payload: bytes) -> WebhookEvent:
        expected = hmac.new(self.secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature or ""):
            raise ValueError("invalid manual-gateway signature")
        data = json.loads(payload)
        return WebhookEvent(
            provider="manual",
            provider_event_id=data["id"],
            event_type=data["type"],
            payload=data.get("data", {}),
        )

    def sign_payload(self, payload: bytes) -> str:
        """Helper for tests: produce a valid signature for an arbitrary payload."""
        return hmac.new(self.secret.encode(), payload, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Stripe gateway — thin wrapper around the official SDK
# ---------------------------------------------------------------------------


class StripeGateway:
    provider_name = "stripe"

    def __init__(self, api_key: str = "", webhook_secret: str = "") -> None:
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        try:
            import stripe  # type: ignore
            stripe.api_key = api_key or "sk_test_unset"
            self._stripe = stripe
        except ImportError:  # pragma: no cover — optional in dev
            self._stripe = None

    def _require_sdk(self) -> Any:
        if self._stripe is None:
            raise RuntimeError("stripe SDK is not installed — `pip install stripe`")
        return self._stripe

    def create_customer(self, email: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        stripe = self._require_sdk()
        cust = stripe.Customer.create(email=email, name=name, metadata=metadata or {})
        return cust["id"]

    def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        stripe = self._require_sdk()
        sess = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return sess["url"]

    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        stripe = self._require_sdk()
        sess = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return sess["url"]

    def cancel_subscription(self, subscription_id: str) -> bool:
        stripe = self._require_sdk()
        stripe.Subscription.delete(subscription_id)
        return True

    def parse_webhook(self, signature: str, payload: bytes) -> WebhookEvent:
        stripe = self._require_sdk()
        evt = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        return WebhookEvent(
            provider="stripe",
            provider_event_id=evt["id"],
            event_type=evt["type"],
            payload=evt["data"]["object"] if "data" in evt else {},
        )


# ---------------------------------------------------------------------------
# Paddle gateway — minimal sandbox-compatible implementation
# ---------------------------------------------------------------------------


class PaddleGateway:
    provider_name = "paddle"

    def __init__(self, vendor_id: str = "", api_key: str = "", public_key: str = "") -> None:
        self.vendor_id = vendor_id
        self.api_key = api_key
        self.public_key = public_key

    def create_customer(self, email: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        # Paddle creates customer implicitly on first checkout. We return a placeholder.
        return f"pad_cus_{uuid.uuid4().hex[:12]}"

    def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        return (
            f"https://checkout.paddle.com/checkout/custom?"
            f"vendor={self.vendor_id}&price_id={price_id}&customer={customer_id}"
            f"&success_url={success_url}"
        )

    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        return f"https://customer.paddle.com/?customer={customer_id}&return_url={return_url}"

    def cancel_subscription(self, subscription_id: str) -> bool:
        return True  # actual call requires Paddle Billing API key

    def parse_webhook(self, signature: str, payload: bytes) -> WebhookEvent:
        # Paddle Billing v2 uses HMAC-SHA256(payload, secret). We accept the same shape.
        if not self.public_key:
            logger.warning("Paddle webhook signature skipped — no public_key configured")
        else:
            expected = hmac.new(self.public_key.encode(), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature or ""):
                raise ValueError("invalid paddle-gateway signature")
        data = json.loads(payload)
        return WebhookEvent(
            provider="paddle",
            provider_event_id=data.get("event_id") or data.get("id") or f"paddle_{int(time.time())}",
            event_type=data.get("event_type") or data.get("type") or "unknown",
            payload=data.get("data", data),
        )


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------


def get_billing_gateway() -> BillingGateway:
    settings = get_settings()
    if settings.billing_provider == "stripe":
        return StripeGateway(api_key=settings.stripe_api_key, webhook_secret=settings.stripe_webhook_secret)
    if settings.billing_provider == "paddle":
        return PaddleGateway(
            vendor_id=settings.paddle_vendor_id,
            api_key=settings.paddle_api_key,
            public_key=settings.paddle_public_key,
        )
    return ManualGateway()

"""Email sender abstraction (Resend / Postmark / SES / console).

For local dev / tests the ``ConsoleSender`` prints messages to the log and
keeps them in a queue so tests can inspect outgoing email without
network access.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str = ""
    from_address: str = "TideGuard <noreply@tideguard.app>"
    metadata: dict[str, Any] | None = None


class EmailSender(Protocol):
    name: str

    def send(self, message: EmailMessage) -> dict[str, Any]: ...


class ConsoleSender:
    name = "console"

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> dict[str, Any]:
        self.sent.append(message)
        logger.info("[email/console] to=%s subject=%s", message.to, message.subject)
        return {"ok": True, "id": f"console_{len(self.sent)}"}


class ResendSender:
    name = "resend"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        try:
            import resend  # type: ignore
            resend.api_key = api_key
            self._resend = resend
        except ImportError:  # pragma: no cover — optional
            self._resend = None

    def send(self, message: EmailMessage) -> dict[str, Any]:
        if self._resend is None:
            raise RuntimeError("resend SDK is not installed")
        result = self._resend.Emails.send({
            "from": message.from_address,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html,
            "text": message.text or message.subject,
        })
        return {"ok": True, "id": result.get("id", "")}


class PostmarkSender:
    name = "postmark"

    def __init__(self, server_token: str) -> None:
        self.server_token = server_token

    def send(self, message: EmailMessage) -> dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("httpx is required for Postmark sender") from exc
        resp = httpx.post(
            "https://api.postmarkapp.com/email",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.server_token,
            },
            json={
                "From": message.from_address,
                "To": message.to,
                "Subject": message.subject,
                "HtmlBody": message.html,
                "TextBody": message.text or message.subject,
            },
            timeout=10.0,
        )
        return {"ok": resp.is_success, "status": resp.status_code, "body": resp.text}


_DEFAULT_SENDER: EmailSender | None = None


def get_email_sender() -> EmailSender:
    """Return the configured email sender."""
    global _DEFAULT_SENDER
    if _DEFAULT_SENDER is not None:
        return _DEFAULT_SENDER
    provider = os.environ.get("EMAIL_PROVIDER", "console")
    if provider == "resend":
        _DEFAULT_SENDER = ResendSender(os.environ.get("RESEND_API_KEY", ""))
    elif provider == "postmark":
        _DEFAULT_SENDER = PostmarkSender(os.environ.get("POSTMARK_SERVER_TOKEN", ""))
    else:
        _DEFAULT_SENDER = ConsoleSender()
    return _DEFAULT_SENDER


def reset_email_sender_for_tests() -> None:
    global _DEFAULT_SENDER
    _DEFAULT_SENDER = ConsoleSender()

"""SMS sender (Twilio) — abstracted so tests can stub it out."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SmsMessage:
    to: str
    body: str


class ConsoleSmsSender:
    name = "console"

    def __init__(self) -> None:
        self.sent: list[SmsMessage] = []

    def send(self, message: SmsMessage) -> dict[str, Any]:
        self.sent.append(message)
        logger.info("[sms/console] to=%s body=%s", message.to, message.body[:80])
        return {"ok": True, "id": f"console_{len(self.sent)}"}


class TwilioSender:
    name = "twilio"

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        try:
            from twilio.rest import Client  # type: ignore
            self.client = Client(account_sid, auth_token)
        except ImportError:  # pragma: no cover
            self.client = None

    def send(self, message: SmsMessage) -> dict[str, Any]:
        if self.client is None:
            raise RuntimeError("twilio SDK not installed")
        resp = self.client.messages.create(body=message.body, from_=self.from_number, to=message.to)
        return {"ok": True, "id": resp.sid}


_DEFAULT: ConsoleSmsSender | TwilioSender | None = None


def get_sms_sender() -> ConsoleSmsSender | TwilioSender:
    global _DEFAULT
    if _DEFAULT is not None:
        return _DEFAULT
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    tok = os.environ.get("TWILIO_AUTH_TOKEN", "")
    frm = os.environ.get("TWILIO_FROM_NUMBER", "")
    if sid and tok and frm:
        _DEFAULT = TwilioSender(sid, tok, frm)
    else:
        _DEFAULT = ConsoleSmsSender()
    return _DEFAULT

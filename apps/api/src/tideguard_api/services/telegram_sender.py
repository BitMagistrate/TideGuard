"""Telegram notifier — thin wrapper around the Bot API.

Re-uses the existing bot token from ``apps/bot``. The class is sync and
keeps a small queue of dispatched messages so tests can inspect them.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TelegramMessage:
    chat_id: str
    text: str
    parse_mode: str = "Markdown"


class TelegramSender:
    name = "telegram"

    def __init__(self, bot_token: str = "") -> None:
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.sent: list[TelegramMessage] = []

    def send(self, message: TelegramMessage) -> dict[str, Any]:
        self.sent.append(message)
        if not self.bot_token:
            logger.info("[telegram/console] chat=%s text=%s", message.chat_id, message.text[:80])
            return {"ok": True, "id": f"console_{len(self.sent)}"}
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        resp = httpx.post(
            url,
            json={
                "chat_id": message.chat_id,
                "text": message.text,
                "parse_mode": message.parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=10.0,
        )
        return {"ok": resp.is_success, "status": resp.status_code, "body": resp.text}


_DEFAULT: TelegramSender | None = None


def get_telegram_sender() -> TelegramSender:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = TelegramSender()
    return _DEFAULT

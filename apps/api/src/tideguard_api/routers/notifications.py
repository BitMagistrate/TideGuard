"""Notification endpoints (§4.2.5) — test channels + delivery log."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from tideguard_api.deps import get_current_user
from tideguard_api.models.user import User
from tideguard_api.services.email_sender import EmailMessage, get_email_sender
from tideguard_api.services.sms_sender import SmsMessage, get_sms_sender
from tideguard_api.services.telegram_sender import TelegramMessage, get_telegram_sender

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TestEmailRequest(BaseModel):
    to: EmailStr
    subject: str = "TideGuard test email"
    body: str = "Hello from TideGuard."


class TestSmsRequest(BaseModel):
    to: str
    body: str = "TideGuard test SMS"


class TestTelegramRequest(BaseModel):
    chat_id: str
    text: str = "TideGuard test message"


@router.post("/email/test")
async def test_email(payload: TestEmailRequest, user: User = Depends(get_current_user)) -> dict:
    sender = get_email_sender()
    try:
        return sender.send(
            EmailMessage(to=str(payload.to), subject=payload.subject, html=f"<p>{payload.body}</p>", text=payload.body)
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"email send failed: {exc}") from exc


@router.post("/sms/test")
async def test_sms(payload: TestSmsRequest, user: User = Depends(get_current_user)) -> dict:
    sender = get_sms_sender()
    try:
        return sender.send(SmsMessage(to=payload.to, body=payload.body))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"sms send failed: {exc}") from exc


@router.post("/telegram/test")
async def test_telegram(payload: TestTelegramRequest, user: User = Depends(get_current_user)) -> dict:
    sender = get_telegram_sender()
    return sender.send(TelegramMessage(chat_id=payload.chat_id, text=payload.text))

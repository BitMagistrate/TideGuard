"""TideGuard Telegram bot entry point.

Audit fixes (TIDEGUARD_AUDIT.md TASK-010 / CRIT-BOT-1..4):

* Use ``httpx.AsyncClient`` instead of the blocking ``httpx.Client`` —
  the synchronous client blocks the asyncio loop and freezes the bot.
* Request a bounding box for ``/forecast`` (the API does not have a
  point-query endpoint) and parse the response shape correctly.
* Allow attaching a photo to ``/report`` via reply-to-message; upload it
  to ``POST /reports`` as ``multipart/form-data``.
* Black-Sea defaults (Anapa) rather than the previous Taiwan defaults.
* Dev-mode dev-token bootstrap so a self-hosted bot can authenticate
  without manual JWT management (only used when ``TIDEGUARD_BOT_DEV_TOKEN``
  is set).
"""

from __future__ import annotations

import io
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class Settings:
    token: str
    api_base: str = "https://api.tideguard.app"
    timeout_s: float = 10.0
    user_agent: str = "tideguard-bot/0.2.0"
    dev_token: Optional[str] = None  # if set, Authorization: Bearer <dev_token>
    default_bbox: str = "37.0,44.0,39.0,46.0"  # Anapa / Novorossiysk

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.environ.get("TIDEGUARD_BOT_TOKEN", "").strip()
        if not token:
            raise SystemExit("TIDEGUARD_BOT_TOKEN is required")
        return cls(
            token=token,
            api_base=os.environ.get("TIDEGUARD_API_BASE", cls.api_base),
            timeout_s=float(os.environ.get("TIDEGUARD_BOT_TIMEOUT", str(cls.timeout_s))),
            dev_token=os.environ.get("TIDEGUARD_BOT_DEV_TOKEN") or None,
            default_bbox=os.environ.get("TIDEGUARD_BOT_DEFAULT_BBOX", cls.default_bbox),
        )


def _api(settings: Settings) -> httpx.AsyncClient:
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    if settings.dev_token:
        headers["Authorization"] = f"Bearer {settings.dev_token}"
    return httpx.AsyncClient(
        base_url=settings.api_base,
        timeout=settings.timeout_s,
        headers=headers,
    )


def _safe_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _bbox_for_point(lat: float, lon: float, *, half_deg: float = 0.25) -> str:
    return f"{lon - half_deg},{lat - half_deg},{lon + half_deg},{lat + half_deg}"


WELCOME = (
    "👋 Привет! Я бот TideGuard — прогноз мусора в Чёрном море.\n\n"
    "/forecast <lat> <lon> — прогноз 5 дней в радиусе 25 км\n"
    "/exceedance <lat> <lon> — карта вероятностей превышения\n"
    "/report <lat> <lon> <severity 1..5> <type> — отправить наблюдение\n"
    "                                              (приложите фото reply-to)\n"
    "/lessons — открытые уроки CC-BY-4.0\n"
    "/cleanup — ближайший плановый сабботник\n"
    "/help — это сообщение\n"
)


def build_app(settings: Settings):  # pragma: no cover — exercised via integration tests
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    application = ApplicationBuilder().token(settings.token).build()

    async def cmd_start(update: Update, _ctx: "ContextTypes.DEFAULT_TYPE"):
        await update.message.reply_text(WELCOME)

    async def cmd_help(update: Update, _ctx: "ContextTypes.DEFAULT_TYPE"):
        await update.message.reply_text(WELCOME)

    async def cmd_forecast(update: Update, ctx: "ContextTypes.DEFAULT_TYPE"):
        args = ctx.args or []
        if len(args) < 2:
            await update.message.reply_text("Usage: /forecast <lat> <lon>")
            return
        lat, lon = _safe_float(args[0]), _safe_float(args[1])
        if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            await update.message.reply_text("Invalid coordinates.")
            return
        bbox = _bbox_for_point(lat, lon)
        async with _api(settings) as client:
            try:
                r = await client.get("/forecast", params={"bbox": bbox, "horizon": 5})
                r.raise_for_status()
                data = r.json()
            except Exception as exc:  # noqa: BLE001
                logger.error("forecast_failed", error=str(exc))
                await update.message.reply_text(f"Не удалось получить прогноз: {exc}")
                return
        days = data.get("days", [])
        if not days:
            await update.message.reply_text("Прогноз пуст.")
            return
        peak_cell = max(days[0]["cells"], key=lambda c: c["concentration"])
        await update.message.reply_text(
            f"📍 ({lat:.4f}, {lon:.4f}) — {data.get('model_version','?')}\n"
            f"Горизонт: {len(days)} дн\n"
            f"Пик дн.1: {peak_cell['concentration']:.2f} в ({peak_cell['lat']:.3f},{peak_cell['lng']:.3f})\n"
            f"Карта: https://tideguard.app/?bbox={bbox}"
        )

    async def cmd_exceedance(update: Update, ctx: "ContextTypes.DEFAULT_TYPE"):
        args = ctx.args or []
        if len(args) < 2:
            await update.message.reply_text("Usage: /exceedance <lat> <lon>")
            return
        lat, lon = _safe_float(args[0]), _safe_float(args[1])
        if lat is None or lon is None:
            await update.message.reply_text("Invalid coordinates.")
            return
        bbox = _bbox_for_point(lat, lon)
        async with _api(settings) as client:
            try:
                r = await client.get(
                    "/forecast/exceedance",
                    params={"bbox": bbox, "horizon": 5, "quantile": 0.9},
                )
                r.raise_for_status()
                data = r.json()
            except Exception as exc:  # noqa: BLE001
                logger.error("exceedance_failed", error=str(exc))
                await update.message.reply_text(f"Не удалось рассчитать вероятность: {exc}")
                return
        cells = data.get("cells", [])
        if not cells:
            await update.message.reply_text("Нет данных.")
            return
        p_max = max(c["probability"] for c in cells)
        await update.message.reply_text(
            f"P(c > q90)={p_max:.0%} в районе ({lat:.4f},{lon:.4f}) — "
            f"{data.get('n_members','?')} участников ансамбля."
        )

    async def cmd_report(update: Update, ctx: "ContextTypes.DEFAULT_TYPE"):
        args = ctx.args or []
        if len(args) < 4:
            await update.message.reply_text(
                "Usage: /report <lat> <lon> <severity 1..5> <type>; reply-to фото для прикрепления."
            )
            return
        lat, lon = _safe_float(args[0]), _safe_float(args[1])
        try:
            severity = int(args[2])
        except ValueError:
            severity = -1
        debris_type = args[3].lower()
        if lat is None or lon is None or not (1 <= severity <= 5):
            await update.message.reply_text("Некорректные параметры.")
            return

        # B15: a photo can come from either (a) a direct photo message with
        # ``caption='/report …'`` or (b) a reply-to a photo.  We check (a)
        # first because it's the more natural flow on mobile (one tap to
        # share + caption, no second message needed).
        photo_bytes: bytes | None = None
        photo_name = "report.jpg"
        direct = update.message
        replied = getattr(update.message, "reply_to_message", None)
        photo_obj = None
        if direct and getattr(direct, "photo", None):
            photo_obj = direct.photo[-1]
        elif (
            direct
            and getattr(direct, "document", None)
            and direct.document.mime_type
            and direct.document.mime_type.startswith("image/")
        ):
            photo_obj = direct.document
        elif replied and replied.photo:
            photo_obj = replied.photo[-1]  # highest resolution
        elif replied and getattr(replied, "document", None) and replied.document.mime_type and replied.document.mime_type.startswith("image/"):
            photo_obj = replied.document
        if photo_obj is not None:
            try:
                tg_file = await photo_obj.get_file()
                buffer = io.BytesIO()
                await tg_file.download_to_memory(out=buffer)
                photo_bytes = buffer.getvalue()
                if hasattr(photo_obj, "file_name") and photo_obj.file_name:
                    photo_name = photo_obj.file_name
            except Exception as exc:  # noqa: BLE001
                logger.warning("photo_download_failed", error=str(exc))

        if photo_bytes is None:
            await update.message.reply_text(
                "Прикрепите фото (reply на фото) — API требует подтверждающее изображение."
            )
            return

        async with _api(settings) as client:
            try:
                files = {"photo": (photo_name, photo_bytes, "image/jpeg")}
                form = {
                    "lat": str(lat),
                    "lng": str(lon),
                    "severity": str(severity),
                    "debris_type": debris_type,
                }
                r = await client.post("/reports", data=form, files=files)
                r.raise_for_status()
                report = r.json()
            except Exception as exc:  # noqa: BLE001
                logger.error("report_failed", error=str(exc))
                await update.message.reply_text(f"Не удалось отправить наблюдение: {exc}")
                return
        await update.message.reply_text(
            f"✅ Принято #{report.get('id','?')[:8]} status={report.get('status','?')} "
            f"phash={report.get('phash','?')[:8]}"
        )

    async def cmd_lessons(update: Update, _ctx: "ContextTypes.DEFAULT_TYPE"):
        async with _api(settings) as client:
            try:
                r = await client.get("/education/lessons")
                r.raise_for_status()
                lessons = r.json()
            except Exception as exc:  # noqa: BLE001
                logger.error("lessons_failed", error=str(exc))
                await update.message.reply_text(f"Не удалось получить уроки: {exc}")
                return
        if not lessons:
            await update.message.reply_text("📚 Уроки пока не загружены. https://tideguard.app/learn")
            return
        titles = "\n".join(f"• {lesson.get('title')}" for lesson in lessons[:10])
        await update.message.reply_text(
            f"📚 {len(lessons)} открытых уроков (CC-BY-4.0):\n{titles}\n\nhttps://tideguard.app/learn"
        )

    async def cmd_cleanup(update: Update, _ctx: "ContextTypes.DEFAULT_TYPE"):
        bbox = settings.default_bbox
        async with _api(settings) as client:
            try:
                r = await client.get("/cleanups", params={"bbox": bbox, "limit": 1})
                r.raise_for_status()
                items = r.json()
                if isinstance(items, dict):
                    items = items.get("items", [])
            except Exception as exc:  # noqa: BLE001
                logger.error("cleanup_failed", error=str(exc))
                await update.message.reply_text(f"Не удалось получить субботники: {exc}")
                return
        if not items:
            await update.message.reply_text(
                "Запланированных субботников пока нет. Проверьте https://tideguard.app/cleanups ."
            )
            return
        ev = items[0]
        await update.message.reply_text(
            f"🧹 Ближайший: {ev.get('id','?')[:8]} kg={ev.get('kg_collected')} "
            f"участников={ev.get('participants')} от {ev.get('created_at','')[:10]}"
        )

    async def fallback(update: Update, _ctx: "ContextTypes.DEFAULT_TYPE"):
        await update.message.reply_text("Неизвестная команда. /help")

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("forecast", cmd_forecast))
    application.add_handler(CommandHandler("exceedance", cmd_exceedance))
    application.add_handler(CommandHandler("report", cmd_report))

    # B15: route photo messages whose caption begins with ``/report`` to
    # the same handler — turns the bot from "reply-to-photo only" into
    # "send-photo-with-caption", which is the natural mobile flow.
    async def cmd_report_with_caption(
        update: Update,
        ctx: "ContextTypes.DEFAULT_TYPE",
    ):
        caption = update.message.caption or ""
        parts = caption.split()
        if parts and parts[0] == "/report":
            ctx.args = parts[1:]
            await cmd_report(update, ctx)

    application.add_handler(
        MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/report\b"), cmd_report_with_caption)
    )
    application.add_handler(CommandHandler("lessons", cmd_lessons))
    application.add_handler(CommandHandler("cleanup", cmd_cleanup))
    application.add_handler(MessageHandler(filters.COMMAND, fallback))
    return application


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    structlog.configure(processors=[structlog.processors.JSONRenderer()])
    settings = Settings.from_env()
    app = build_app(settings)
    app.run_polling()
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["Settings", "build_app", "main", "_bbox_for_point", "_safe_float"]

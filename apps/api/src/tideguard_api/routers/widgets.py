"""Embeddable widget endpoints (§5.3) — HTML snippet, JSON, QR."""

from __future__ import annotations

import io
from datetime import UTC, datetime

from fastapi import APIRouter, Response

from tideguard_api.schemas.widgets import BeachStatusJson
from tideguard_api.services.esg_risk_engine import compute_risk

router = APIRouter(prefix="/widgets", tags=["widgets"])

_HTML_TEMPLATE = """<!doctype html>
<html lang="{lang}"><head>
<meta charset="utf-8">
<title>TideGuard — {name}</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;padding:0;background:{bg};color:{fg};}}
 .card{{width:300px;height:200px;border-radius:12px;padding:16px;box-sizing:border-box;
        background:{bg};border:1px solid {border};box-shadow:0 4px 10px rgba(0,0,0,.08);}}
 .status{{font-size:28px;font-weight:700;color:{accent};}}
 .score{{font-size:14px;color:{fg};margin-top:4px;}}
 .forecast{{margin-top:12px;display:flex;gap:8px;}}
 .day{{flex:1;text-align:center;font-size:11px;padding:4px;border-radius:6px;background:{day_bg};}}
 .footer{{margin-top:10px;font-size:11px;color:#888;}}
 .footer a{{color:#888;text-decoration:underline;}}
</style></head>
<body><div class="card">
<div class="status">{status}</div>
<div class="score">{cleanliness_pct}% чистоты · {as_of}</div>
<div class="forecast">{forecast_html}</div>
<div class="footer">Powered by <a href="https://tideguard.app" target="_blank" rel="noopener">TideGuard</a></div>
</div></body></html>"""


def _make_widget_payload(lat: float, lng: float, horizon: int) -> BeachStatusJson:
    rs = compute_risk(lat, lng, horizon_years=1)
    cleanliness = max(5, 100 - rs.score)
    status = "Clean" if cleanliness >= 70 else ("Watch" if cleanliness >= 45 else "Alert")
    forecast = [
        {
            "day": (datetime.now(UTC).date()).isoformat(),
            "cleanliness_pct": cleanliness,
            "p_exceed": rs.components["frequency_p90_5y_mean"],
        }
    ]
    for d in range(1, horizon):
        forecast.append(
            {
                "day": (datetime.now(UTC).date()).isoformat(),
                "cleanliness_pct": max(5, cleanliness - d * 2),
                "p_exceed": min(0.99, rs.components["frequency_p90_5y_mean"] + d * 0.02),
            }
        )
    return BeachStatusJson(
        lat=lat,
        lng=lng,
        status=status.lower(),
        cleanliness_score=cleanliness / 100.0,
        forecast=forecast,
        as_of=datetime.now(UTC).isoformat(),
    )


@router.get("/beach_status.json", response_model=BeachStatusJson)
async def beach_status_json(lat: float, lng: float, horizon: int = 3) -> BeachStatusJson:
    return _make_widget_payload(lat, lng, horizon)


@router.get("/beach_status", response_class=Response)
async def beach_status_html(
    lat: float,
    lng: float,
    horizon: int = 3,
    theme: str = "light",
    lang: str = "en",
) -> Response:
    payload = _make_widget_payload(lat, lng, horizon)
    name = f"{lat:.3f}, {lng:.3f}"
    cleanliness_pct = int(payload.cleanliness_score * 100)
    label = {"en": {"clean": "Clean", "watch": "Watch", "alert": "Alert"},
             "ru": {"clean": "Чисто", "watch": "Внимание", "alert": "Загрязнение"}}.get(lang, {})
    status_text = label.get(payload.status, payload.status.title())
    bg, fg, border, accent, day_bg = (
        ("#fff", "#111", "#e5e7eb", "#10b981", "#f3f4f6") if theme == "light"
        else ("#0f172a", "#f8fafc", "#1e293b", "#34d399", "#1e293b")
    )
    if payload.status == "watch":
        accent = "#f59e0b"
    elif payload.status == "alert":
        accent = "#ef4444"
    forecast_html = "".join(
        f'<div class="day"><div>{i}d</div><div>{int(f["cleanliness_pct"])}%</div></div>'
        for i, f in enumerate(payload.forecast)
    )
    html = _HTML_TEMPLATE.format(
        lang=lang,
        name=name,
        bg=bg, fg=fg, border=border, accent=accent, day_bg=day_bg,
        status=status_text,
        cleanliness_pct=cleanliness_pct,
        as_of=payload.as_of[:10],
        forecast_html=forecast_html,
    )
    return Response(
        content=html, media_type="text/html",
        headers={"Cache-Control": "public, max-age=3600", "X-Powered-By": "TideGuard"},
    )


@router.get("/beach_status/qr")
async def beach_status_qr(lat: float, lng: float, hotel_id: str = "") -> Response:
    try:
        import qrcode  # type: ignore
    except ImportError:  # pragma: no cover
        return Response(b"qrcode unavailable", status_code=503)
    url = f"https://tideguard.app/beach?lat={lat}&lng={lng}"
    if hotel_id:
        url += f"&hotel_id={hotel_id}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/adopted_beach")
async def adopted_beach_widget(segment_id: str, theme: str = "light") -> Response:
    # Lightweight placeholder snippet — points users at the adopter page.
    html = (
        "<!doctype html><html><body>"
        f"<div style='font-family:system-ui;padding:12px;border:1px solid #e5e7eb;border-radius:8px;width:300px'>"
        f"<strong>Beach under protection</strong><br>"
        f"<small>segment <code>{segment_id}</code> · Powered by <a href='https://tideguard.app'>TideGuard</a></small>"
        f"</div></body></html>"
    )
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "public, max-age=3600"})


@router.get("/adopted_beach/qr")
async def adopted_beach_qr(segment_id: str) -> Response:
    try:
        import qrcode  # type: ignore
    except ImportError:  # pragma: no cover
        return Response(b"qrcode unavailable", status_code=503)
    img = qrcode.make(f"https://tideguard.app/beach/{segment_id}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

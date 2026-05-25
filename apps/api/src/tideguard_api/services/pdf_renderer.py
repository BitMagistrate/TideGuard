"""PDF renderer.

The plan asks for WeasyPrint (HTML+CSS → PDF) so designers can iterate on
templates. WeasyPrint depends on libpango / libcairo at the system level
and may not be present in all dev environments — so we fall back to
ReportLab and finally to a plain-text PDF if neither is available.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    enable_async=False,
)


def render_html(template_name: str, context: dict[str, Any]) -> str:
    return _jinja.get_template(template_name).render(**context)


def render_pdf_from_html(html: str) -> bytes:
    """Return PDF bytes from HTML.

    Prefer WeasyPrint; fall back to a ReportLab text dump when the system
    libraries are missing (e.g. during CI).
    """
    try:
        from weasyprint import HTML  # type: ignore
        return HTML(string=html).write_pdf()  # type: ignore[no-any-return]
    except Exception as exc:  # noqa: BLE001
        logger.info("WeasyPrint unavailable (%s) — falling back to ReportLab", exc)
        return _reportlab_fallback(html)


def _reportlab_fallback(html: str) -> bytes:
    """ReportLab fallback: strip tags and render as a text-only PDF."""
    import re

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+\n", "\n", text)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 20 * mm
    c.setFont("Helvetica", 10)
    for line in text.splitlines():
        if y < 20 * mm:
            c.showPage()
            y = h - 20 * mm
            c.setFont("Helvetica", 10)
        for chunk in _wrap(line, 100):
            c.drawString(15 * mm, y, chunk[:200])
            y -= 5 * mm
    c.save()
    return buf.getvalue()


def _wrap(line: str, width: int) -> list[str]:
    if len(line) <= width:
        return [line] if line else [""]
    out: list[str] = []
    while line:
        out.append(line[:width])
        line = line[width:]
    return out


def render_template_to_pdf(template_name: str, context: dict[str, Any]) -> bytes:
    html = render_html(template_name, context)
    return render_pdf_from_html(html)

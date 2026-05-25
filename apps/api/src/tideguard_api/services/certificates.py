"""PDF certificate generation + verifiable-hash helpers (TASK-013)."""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date


def compute_certificate_hash(
    user_id: str,
    user_email: str,
    completed_lessons: list[dict],
    issue_date: str | None = None,
    git_sha: str = "v0.2.0",
) -> str:
    """SHA-256 hash of the canonical certificate payload."""
    payload = {
        "user_id": str(user_id),
        "user_email": user_email,
        "issue_date": issue_date or date.today().isoformat(),
        "git_sha": git_sha,
        "lessons": sorted(
            ({"slug": le["slug"], "score": round(float(le["score"]), 4)} for le in completed_lessons),
            key=lambda x: x["slug"],
        ),
    }
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()


@dataclass
class CertificatePayload:
    user_name: str
    school_name: str | None
    completed_lessons: int
    issue_date: date
    cert_hash: str


def render_certificate_pdf(
    user_name: str,
    school_name: str | None,
    completed_lessons: int,
    issue_date: date | None = None,
    cert_hash: str | None = None,
) -> bytes:
    """Render an A4 landscape certificate as a PDF (via reportlab)."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    if issue_date is None:
        issue_date = date.today()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    w, h = landscape(A4)

    c.setFillColorRGB(0.06, 0.46, 0.43)
    c.rect(0, h - 40 * mm, w, 40 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(20 * mm, h - 28 * mm, "TideGuard EE Certificate")

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 16)
    c.drawString(20 * mm, h - 60 * mm, "This certifies that")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, h - 75 * mm, user_name)
    c.setFont("Helvetica", 14)
    if school_name:
        c.drawString(20 * mm, h - 88 * mm, f"of {school_name}")
    c.drawString(
        20 * mm,
        h - 105 * mm,
        f"completed {completed_lessons} lessons of the TideGuard Environmental Education programme",
    )
    c.drawString(20 * mm, h - 117 * mm, f"with a passing score (≥0.70) in each lesson on {issue_date.isoformat()}.")

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, 20 * mm, "Issued by TideGuard AI — open-source, MIT-licensed.")
    if cert_hash:
        c.setFont("Courier", 8)
        c.drawString(20 * mm, 14 * mm, f"Verify at https://tideguard.app/education/certificate/verify/{cert_hash}")

    c.showPage()
    c.save()
    return buffer.getvalue()

"""Photo upload service.

Hardened per TIDEGUARD_AUDIT.md (TASK-006, CRIT-API-5..7):
  * MIME / size validated up-front (request-body limit enforced by middleware).
  * EXIF / GPS stripping uses Pillow's `save(exif=b"")` instead of an
    O(N) `putdata(list(getdata()))` rebuild — no 30-50× RAM blow-up.
  * In production / staging, EXIF-strip failure on a real-MIME upload
    raises HTTPException(415) rather than silently storing the original.
  * Optional GPS cross-check against the user-provided coordinates.
  * Returns the URL + a perceptual hash (used by callers for dedup).
"""

from __future__ import annotations

import hashlib
import io
import logging
import math
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import ExifTags, Image, UnidentifiedImageError

from tideguard_api.settings import get_settings

logger = logging.getLogger(__name__)


def _suffix_for_mime(mime: str | None) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }.get((mime or "").lower(), ".jpg")


def _pil_format(mime: str | None) -> str:
    return {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
        "image/heic": "HEIF",
    }.get((mime or "").lower(), "JPEG")


_GPS_TAG = next((k for k, v in ExifTags.TAGS.items() if v == "GPSInfo"), 0x8825)


def _gps_to_decimal(raw, ref: str) -> float | None:
    """Convert EXIF GPS rationals to a signed decimal degree."""
    try:
        d, m, s = raw
        deg = float(d[0]) / float(d[1]) if isinstance(d, tuple) else float(d)
        mn = float(m[0]) / float(m[1]) if isinstance(m, tuple) else float(m)
        sc = float(s[0]) / float(s[1]) if isinstance(s, tuple) else float(s)
        value = deg + mn / 60.0 + sc / 3600.0
        if ref in ("S", "W"):
            value = -value
        return value
    except Exception:  # noqa: BLE001
        return None


@dataclass
class ExtractedGPS:
    lat: float | None
    lng: float | None

    @property
    def present(self) -> bool:
        return self.lat is not None and self.lng is not None


def _extract_gps(img: Image.Image) -> ExtractedGPS:
    try:
        exif = img.getexif()
        if not exif:
            return ExtractedGPS(None, None)
        gps_ifd = exif.get_ifd(_GPS_TAG) or {}
        if not gps_ifd:
            return ExtractedGPS(None, None)
        # 1=N, 2=lat, 3=E, 4=lng
        lat_ref = gps_ifd.get(1)
        lat_raw = gps_ifd.get(2)
        lng_ref = gps_ifd.get(3)
        lng_raw = gps_ifd.get(4)
        if not (lat_ref and lat_raw and lng_ref and lng_raw):
            return ExtractedGPS(None, None)
        return ExtractedGPS(
            lat=_gps_to_decimal(lat_raw, str(lat_ref)),
            lng=_gps_to_decimal(lng_raw, str(lng_ref)),
        )
    except Exception:  # noqa: BLE001
        return ExtractedGPS(None, None)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    p = math.pi / 180.0
    a = (
        0.5
        - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def _phash_hex(img: Image.Image) -> str:
    """8x8 average-hash fingerprint — fast, dep-free, good for near-dup detection."""
    try:
        small = img.convert("L").resize((8, 8), Image.Resampling.BILINEAR)
        pixels = list(small.getdata())
        avg = sum(pixels) / 64.0
        bits = 0
        for i, p in enumerate(pixels):
            if p > avg:
                bits |= 1 << i
        return f"{bits:016x}"
    except Exception:  # noqa: BLE001
        return ""


def _strip_exif(data: bytes, mime: str | None) -> tuple[bytes, ExtractedGPS, str]:
    """Return (clean_bytes, gps_before_strip, phash).

    In production / staging we *must* be able to parse the image. If Pillow
    raises ``UnidentifiedImageError`` on a real image MIME, we now raise an
    HTTPException(415) instead of silently storing the original bytes
    (which broke the privacy guarantee — CRIT-API-6).
    """
    settings = get_settings()
    strict = settings.env in ("production", "staging")

    try:
        bio = io.BytesIO(data)
        img: Image.Image = Image.open(bio).copy()
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        if strict:
            raise HTTPException(415, f"Cannot parse image for EXIF strip: {exc}") from exc
        logger.info("EXIF strip skipped (non-strict env, non-image data): %s", exc)
        return data, ExtractedGPS(None, None), ""

    gps = _extract_gps(img)
    phash = _phash_hex(img)

    out = io.BytesIO()
    fmt = _pil_format(mime) if mime else (img.format or "JPEG")
    save_kwargs: dict = {"exif": b""}
    save_img = img
    if fmt == "JPEG":
        save_img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
        save_kwargs["quality"] = 92
    try:
        save_img.save(out, format=fmt, **save_kwargs)
    except (OSError, ValueError, KeyError) as exc:
        if strict:
            raise HTTPException(415, f"EXIF-strip save failed: {exc}") from exc
        logger.info("EXIF strip save failed in non-strict env: %s", exc)
        return data, gps, phash

    return out.getvalue(), gps, phash


def _scan_clamav(body: bytes) -> None:
    settings = get_settings()
    if not settings.clamav_socket:
        return
    try:  # pragma: no cover — optional sidecar
        import clamd

        scanner = clamd.ClamdUnixSocket(settings.clamav_socket)
        verdict = scanner.instream(io.BytesIO(body))
        result = verdict.get("stream") if isinstance(verdict, dict) else None
        if result and result[0] == "FOUND":
            raise HTTPException(415, f"Malware detected: {result[1]}")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("ClamAV scan failed open: %s", exc)


def _validate(photo: UploadFile, body: bytes) -> None:
    settings = get_settings()
    if len(body) == 0:
        raise HTTPException(400, "Empty photo body")
    if len(body) > settings.photo_max_bytes:
        raise HTTPException(
            413, f"Photo exceeds {settings.photo_max_bytes // (1024 * 1024)} MB limit"
        )
    mime = (photo.content_type or "").lower()
    if mime and mime not in settings.photo_allowed_mime:
        raise HTTPException(
            415, f"Unsupported media type {photo.content_type!r}; allowed: {settings.photo_allowed_mime}"
        )


@dataclass
class UploadResult:
    url: str
    phash: str
    gps_present: bool
    gps_mismatch_m: float | None


async def upload_photo(
    photo: UploadFile,
    user_id: uuid.UUID,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> UploadResult:
    """Validate, EXIF-strip, AV-scan and upload a photo.

    When ``user_lat / user_lng`` is supplied and the EXIF has a GPS tag, we
    compute the Haversine delta. If it exceeds
    ``settings.photo_gps_tolerance_meters`` we flag the upload as suspect
    (the API caller decides what to do with it — typically force-moderate).
    """
    settings = get_settings()
    body = await photo.read()
    _validate(photo, body)
    _scan_clamav(body)
    body, gps, phash = _strip_exif(body, photo.content_type)

    gps_delta: float | None = None
    if gps.present and user_lat is not None and user_lng is not None:
        gps_delta = _haversine_m(gps.lat or 0.0, gps.lng or 0.0, user_lat, user_lng)
        if gps_delta > settings.photo_gps_tolerance_meters:
            logger.info(
                "Photo GPS mismatch for user=%s: %.0f m > tolerance %.0f m",
                user_id,
                gps_delta,
                settings.photo_gps_tolerance_meters,
            )

    suffix = _suffix_for_mime(photo.content_type) or Path(photo.filename or "image.jpg").suffix or ".jpg"
    sha = hashlib.sha256(body).hexdigest()[:16]
    object_key = f"reports/{user_id}/{uuid.uuid4().hex}-{sha}{suffix}"

    if settings.s3_endpoint and settings.s3_access_key:
        url = _put_s3(object_key, body, photo.content_type)
    else:
        local_dir = Path("uploads") / "photos"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / object_key.replace("/", "_")
        local_path.write_bytes(body)
        url = f"/uploads/photos/{local_path.name}"

    return UploadResult(url=url, phash=phash, gps_present=gps.present, gps_mismatch_m=gps_delta)


def _s3_client():
    """Return a boto3 S3 client configured from settings.

    Lazily imports boto3 so non-S3 deployments don't pay the import cost.
    """
    settings = get_settings()
    import boto3  # type: ignore

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key or None,
        aws_secret_access_key=settings.s3_secret_key or None,
    )


def _put_s3(object_key: str, body: bytes, mime: str | None) -> str:
    """Upload ``body`` to the configured S3 bucket and return a public URL."""
    settings = get_settings()
    client = _s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_photos,
        Key=object_key,
        Body=body,
        ContentType=mime or "image/jpeg",
    )
    return f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket_photos}/{object_key}"


def presigned_get_url(object_key: str, expires_in: int = 3600) -> str | None:
    """Return a presigned S3 GET URL for the given object, or ``None``
    when S3 is not configured.

    Used by callers that need a short-lived public URL (e.g. embedding
    photos in a B2G PDF report).  The default TTL is 1 hour — adjust
    via ``expires_in`` for longer-lived workflows.
    """
    settings = get_settings()
    if not (settings.s3_endpoint and settings.s3_access_key):
        return None
    client = _s3_client()
    try:
        url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.s3_bucket_photos, "Key": object_key},
            ExpiresIn=int(expires_in),
        )
        return str(url) if url is not None else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to generate presigned URL for %s: %s", object_key, exc)
        return None


def presigned_put_url(
    object_key: str,
    expires_in: int = 600,
    mime: str = "image/jpeg",
) -> str | None:
    """Return a presigned S3 PUT URL so clients can upload directly.

    The recommended flow is: client requests a presigned PUT URL, then
    uploads the file straight to S3 (bypassing the API), and finally
    calls ``POST /reports`` with the resulting object key.
    """
    settings = get_settings()
    if not (settings.s3_endpoint and settings.s3_access_key):
        return None
    client = _s3_client()
    try:
        url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.s3_bucket_photos,
                "Key": object_key,
                "ContentType": mime,
            },
            ExpiresIn=int(expires_in),
        )
        return str(url) if url is not None else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to generate presigned PUT URL for %s: %s", object_key, exc)
        return None

"""Generate favicon and og-image used by the Next.js web dashboard."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "apps/web/public"
PUBLIC.mkdir(parents=True, exist_ok=True)


def teal_wave(width: int, height: int) -> Image.Image:
    """Return an RGB image with a stylised wave gradient + light foam."""
    img = Image.new("RGB", (width, height), "#e0f2fe")
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        r = int((1 - t) * 224 + t * 15)
        g = int((1 - t) * 242 + t * 118)
        b = int((1 - t) * 254 + t * 110)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def favicon() -> None:
    sizes = [16, 32, 48, 64]
    images = []
    for size in sizes:
        img = teal_wave(size, size)
        draw = ImageDraw.Draw(img)
        # Stylised T mark in the centre.
        margin = max(size // 6, 1)
        draw.rectangle(
            [margin, margin, size - margin, margin + max(size // 6, 1)], fill="#0f766e"
        )
        draw.rectangle(
            [
                size // 2 - max(size // 12, 1),
                margin,
                size // 2 + max(size // 12, 1),
                size - margin,
            ],
            fill="#0f766e",
        )
        images.append(img)
    images[0].save(PUBLIC / "favicon.ico", sizes=[(s, s) for s in sizes])
    # 32x32 PNG variant for modern browsers.
    img32 = teal_wave(32, 32)
    draw = ImageDraw.Draw(img32)
    draw.rectangle([4, 4, 28, 8], fill="#0f766e")
    draw.rectangle([14, 4, 18, 28], fill="#0f766e")
    img32.save(PUBLIC / "favicon-32x32.png")


def og_image() -> None:
    w, h = 1200, 630
    img = teal_wave(w, h)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70
        )
        font_med = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
        )
    except OSError:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((60, 80), "TideGuard AI", fill="#0f766e", font=font_big)
    draw.text(
        (60, 200),
        "Physics-informed forecasts of floating marine debris",
        fill="#0f4663",
        font=font_med,
    )
    draw.text(
        (60, 250),
        "Russian Black Sea pilot · open source · for and by youth",
        fill="#0f4663",
        font=font_med,
    )

    draw.rectangle([60, 480, 1140, 482], fill="#0f766e")
    draw.text(
        (60, 510),
        "github.com/desirewarlockstaple/mnohyjmg",
        fill="#0f4663",
        font=font_small,
    )
    draw.text(
        (60, 545),
        "Built solo by Ермоленко Владимир Александрович · Гимназия №13 «Академ»",
        fill="#0f4663",
        font=font_small,
    )
    img.save(PUBLIC / "og-image.png")


def robots() -> None:
    (PUBLIC / "robots.txt").write_text("""User-agent: *
Allow: /
Sitemap: https://tideguard.app/sitemap.xml
""")


def main() -> None:
    favicon()
    og_image()
    robots()
    print(f"Wrote favicon / og-image / robots.txt into {PUBLIC}")


if __name__ == "__main__":
    main()

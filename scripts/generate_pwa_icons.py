"""One-shot generator for PySynth's PWA icons.

Produces four PNGs in `frontend/public/`:
- icon-192.png             — Android home-screen
- icon-512.png             — Android splash / larger surfaces
- icon-512-maskable.png    — Android adaptive (safe zone padded)
- apple-touch-icon.png     — iOS home-screen (180×180), required for PWA install

Visual: dark background, cyan rounded square plate, "PS" wordmark.
Run manually: `python scripts/generate_pwa_icons.py`
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BG = (2, 2, 3, 255)         # near-black, matches manifest background_color
CYAN = (0, 245, 255, 255)   # matches manifest theme_color
TEXT = (8, 12, 18, 255)     # very dark slate so "PS" reads on cyan
OUT_DIR = Path(__file__).resolve().parents[1] / "frontend" / "public"


def _pick_font(size: int) -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_icon(size: int, *, padding_ratio: float = 0.0) -> Image.Image:
    """Square icon with a cyan plate + "PS" text.

    padding_ratio=0.12 reserves the maskable safe zone (Android crops up to ~10%
    on adaptive icons; 12% is conservative)."""
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    pad = int(size * padding_ratio)
    plate_inset = pad + int(size * 0.10)
    radius = int(size * 0.18)
    draw.rounded_rectangle(
        (plate_inset, plate_inset, size - plate_inset, size - plate_inset),
        radius=radius,
        fill=CYAN,
    )

    text = "PS"
    font = _pick_font(int(size * 0.42))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - int(size * 0.02)
    draw.text((tx, ty), text, font=font, fill=TEXT)
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        ("icon-192.png", 192, 0.0),
        ("icon-512.png", 512, 0.0),
        ("icon-512-maskable.png", 512, 0.12),
        ("apple-touch-icon.png", 180, 0.0),
    ]
    for name, size, pad in targets:
        path = OUT_DIR / name
        _draw_icon(size, padding_ratio=pad).save(path, "PNG")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()

"""One-shot generator for PySynth's PWA icons.

Loads `scripts/reference.icon.png` (the user-supplied Python-logo + code-editor
artwork), center-crops it to square, downsamples to each target size with
LANCZOS so the result is sharp, and overlays a subtle `by: JP` watermark in
the bottom-right corner.

Outputs in `frontend/public/`:
- icon-192.png             — Android home-screen
- icon-512.png             — Android splash / larger surfaces
- icon-512-maskable.png    — Android adaptive (safe zone padded)
- apple-touch-icon.png     — iOS home-screen (180×180), required for PWA install

Run manually: `python scripts/generate_pwa_icons.py`
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SCRIPTS_DIR = Path(__file__).resolve().parent
SOURCE = SCRIPTS_DIR / "reference.icon.png"
OUT_DIR = SCRIPTS_DIR.parent / "frontend" / "public"

WATERMARK_RGBA = (255, 255, 255, 200)
WATERMARK_SHADOW = (0, 0, 0, 220)
# Sampled near the corners of the reference so the maskable-variant padding
# blends with the artwork instead of showing a hard seam.
BG_DARK = (10, 24, 32, 255)


def _pick_sans_bold(size: int) -> ImageFont.ImageFont:
    for name in ("seguibl.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _square_crop(src: Image.Image) -> Image.Image:
    """Center-crop to a square using the smaller of width/height."""
    w, h = src.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return src.crop((left, top, left + side, top + side))


def _add_watermark(img: Image.Image) -> None:
    """'by: JP' tag, bottom-right corner — small, semi-transparent, with a
    drop shadow so it stays readable at home-screen render sizes without
    covering the Python-logo subject. Mutates `img`."""
    size = img.size[0]
    draw = ImageDraw.Draw(img, "RGBA")
    font = _pick_sans_bold(max(7, int(size * 0.032)))
    text = "by: JP"

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Sit in the dark wedge between the yellow snake's bottom-right curve
    # and the icon's edge. The wedge is narrow — the snake's bottom edge
    # comes close to the icon bottom — so the watermark has to be quite
    # small AND positioned with care: bigger horizontal inset moves it
    # toward icon-center (where the wedge is thinnest), bigger vertical
    # inset moves it up (toward the snake). These two values are tuned
    # so the text lands fully inside the wedge without touching either
    # the snake or the iOS-mask clip zone.
    pad_right = int(size * 0.25)
    pad_bottom = int(size * 0.12)
    x = size - tw - pad_right - bbox[0]
    y = size - th - pad_bottom - bbox[1]

    # Shadow + text — no pill backing this time, just the text floating
    # so the artwork shows through underneath.
    shadow_offset = max(1, size // 220)
    draw.text((x + shadow_offset, y + shadow_offset),
              text, font=font, fill=WATERMARK_SHADOW)
    draw.text((x, y), text, font=font, fill=WATERMARK_RGBA)


def _padded_for_maskable(square: Image.Image, target_size: int, pad_ratio: float) -> Image.Image:
    """Wrap the square artwork in a same-colored background so Android's
    adaptive-icon crop (circle, squircle, etc.) doesn't eat the logo."""
    canvas = Image.new("RGBA", (target_size, target_size), BG_DARK)
    inner_size = target_size - 2 * int(target_size * pad_ratio)
    inner = square.resize((inner_size, inner_size), Image.LANCZOS).convert("RGBA")
    pad = (target_size - inner_size) // 2
    canvas.paste(inner, (pad, pad), inner)
    return canvas


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(
            f"Missing source artwork at {SOURCE}. Save the reference image there first."
        )
    src = Image.open(SOURCE).convert("RGBA")
    square = _square_crop(src)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Non-maskable variants: resize the cropped square directly, watermark
    # in the bottom-right.
    plain_targets = [
        ("icon-192.png", 192),
        ("icon-512.png", 512),
        ("apple-touch-icon.png", 180),
    ]
    for name, size in plain_targets:
        out = square.resize((size, size), Image.LANCZOS).convert("RGBA")
        _add_watermark(out)
        path = OUT_DIR / name
        out.save(path, "PNG")
        print(f"wrote {path}")

    # Maskable variant: add 14% safe-zone padding so Android can crop with
    # any shape without losing the snakes or the watermark.
    maskable = _padded_for_maskable(square, 512, pad_ratio=0.14)
    _add_watermark(maskable)
    path = OUT_DIR / "icon-512-maskable.png"
    maskable.save(path, "PNG")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()

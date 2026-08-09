"""16 ta MBTI tipi uchun Open Graph rasmlarini yaratadi (1200x630 PNG).

Rasmlar `app/static/images/og/` ga yoziladi va repoga qo'shiladi — ish vaqtida
generatsiya ham, shrift fayli ham kerak bo'lmaydi. Shrift faqat shu skript uchun
kerak, shuning uchun u repoga emas, lokal keshga yuklab olinadi.

Ishga tushirish:
    python scripts/generate_og_images.py
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "app" / "static" / "images" / "og"
FONT_CACHE = ROOT / ".fontcache"

# Inter — SIL Open Font License. Shrift repoga kirmaydi: Google Fonts TTF havolasi
# versiya bilan o'zgaradi, shuning uchun u CSS API orqali aniqlanadi.
FONT_CSS_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;700"
FONT_WEIGHTS = {"regular": "400", "bold": "700"}
# TTF qaytishi uchun eski brauzer sifatida murojaat qilinadi (woff2 emas).
_LEGACY_UA = {"User-Agent": "Mozilla/4.0"}

WIDTH, HEIGHT = 1200, 630
MARGIN = 80

NAVY = (11, 35, 72)
NAVY_SOFT = (24, 56, 104)
CREAM = (255, 253, 248)
GOLD = (201, 138, 34)
MUTED = (150, 168, 196)

DIMENSIONS = (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))

ALL_TYPES = [
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
]

BRAND = "Xarakter testi"
TAGLINE = "24 ta savol · 4 daqiqa"


def _ttf_urls() -> dict[str, str]:
    request = urllib.request.Request(FONT_CSS_URL, headers=_LEGACY_UA)
    with urllib.request.urlopen(request, timeout=60) as response:
        css = response.read().decode("utf-8")
    blocks = css.split("@font-face")
    urls: dict[str, str] = {}
    for name, weight in FONT_WEIGHTS.items():
        for block in blocks:
            if f"font-weight: {weight};" not in block:
                continue
            match = re.search(r"url\((https://[^)]+\.ttf)\)", block)
            if match:
                urls[name] = match.group(1)
                break
        if name not in urls:
            raise OSError(f"Inter {weight} uchun TTF havolasi topilmadi")
    return urls


def _font_path(name: str, url: str) -> Path:
    FONT_CACHE.mkdir(exist_ok=True)
    path = FONT_CACHE / f"inter-{name}.ttf"
    if not path.exists():
        print(f"Shrift yuklanmoqda: {name} ...")
        with urllib.request.urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    return path


def _load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    urls = _ttf_urls()
    bold = _font_path("bold", urls["bold"])
    regular = _font_path("regular", urls["regular"])
    return {
        "type": ImageFont.truetype(str(bold), 190),
        "brand": ImageFont.truetype(str(bold), 30),
        "tagline": ImageFont.truetype(str(regular), 28),
        "dimension": ImageFont.truetype(str(bold), 34),
    }


def _draw_dimension_strip(draw: ImageDraw.ImageDraw, mbti: str, fonts: dict, y: int) -> None:
    """Tipning to'rt harfini o'z o'lchovi bilan ko'rsatadi: E/I, S/N, T/F, J/P."""
    slot = (WIDTH - 2 * MARGIN) // 4
    for index, (left, right) in enumerate(DIMENSIONS):
        x = MARGIN + index * slot
        chosen = mbti[index]
        for offset, letter in ((0, left), (52, right)):
            active = letter == chosen
            draw.text(
                (x + offset, y),
                letter,
                font=fonts["dimension"],
                fill=GOLD if active else MUTED,
            )


def build_image(mbti: str, fonts: dict) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)

    # Yumshoq diagonal urg'u — yalang'och to'q fon o'rniga.
    draw.polygon([(WIDTH, 0), (WIDTH, HEIGHT), (WIDTH - 420, HEIGHT)], fill=NAVY_SOFT)

    draw.text((MARGIN, MARGIN - 20), BRAND, font=fonts["brand"], fill=GOLD)
    draw.text((MARGIN, HEIGHT - MARGIN - 34), TAGLINE, font=fonts["tagline"], fill=MUTED)

    draw.text((MARGIN, 170), mbti, font=fonts["type"], fill=CREAM)
    _draw_dimension_strip(draw, mbti, fonts, y=430)

    return image


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fonts = _load_fonts()
    except OSError as error:
        print(f"Shriftni olishda xato: {error}", file=sys.stderr)
        return 1

    for mbti in ALL_TYPES:
        target = OUTPUT_DIR / f"{mbti}.png"
        build_image(mbti, fonts).save(target, format="PNG", optimize=True)
        print(f"  {target.relative_to(ROOT)}  ({target.stat().st_size // 1024} KB)")

    print(f"{len(ALL_TYPES)} ta rasm yaratildi: {OUTPUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""PDF hisobot uchun shriftlarni yuklab olib, kerakli glifларгаcha qisqartiradi.

To'liq Inter TTF ~320 KB; bizga faqat lotin, kirill va tinish belgilari kerak,
shuning uchun subset ~60 KB bo'ladi va repoda saqlansa ham og'irlik qilmaydi.
Natija `app/pdf/fonts/` ga yoziladi va commit qilinadi — ish vaqtida tarmoq kerak emas.

Ishga tushirish (fontTools kerak, u requirements-dev.txt da):
    python scripts/fetch_pdf_fonts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_og_images import _font_path, _ttf_urls

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "app" / "pdf" / "fonts"

# Lotin + o'zbek diakritikasi + kirill + hisobotda ishlatiladigan tinish belgilari.
UNICODE_RANGES = (
    "U+0020-007E",  # ASCII
    "U+00A0-00FF",  # Latin-1 qo'shimchasi
    "U+0100-017F",  # kengaytirilgan lotin A (o'zbekcha harflar)
    "U+02BB-02BC",  # o'zbek tutuq belgisi
    "U+0400-045F",  # kirill
    "U+0490-0491",  # ukrain g'
    "U+2010-2027",  # tire, qo'shtirnoq, ellipsis
    "U+20AC",  # evro
    "U+2192",  # o'ng strelka
    "U+2022",  # bullet
    "U+00B7",  # o'rta nuqta
)


def _subset(source: Path, target: Path) -> None:
    font = TTFont(str(source))
    options = subset.Options()
    options.layout_features = ["*"]
    options.drop_tables += ["DSIG"]
    options.recalc_bounds = True
    options.notdef_outline = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=subset.parse_unicodes(",".join(UNICODE_RANGES)))
    subsetter.subset(font)
    target.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(target))
    font.close()


def main() -> int:
    try:
        urls = _ttf_urls()
    except OSError as error:
        print(f"Shrift havolasini olishda xato: {error}", file=sys.stderr)
        return 1

    for name in ("regular", "bold"):
        source = _font_path(name, urls[name])
        target = OUTPUT_DIR / f"Inter-{name.capitalize()}.ttf"
        _subset(source, target)
        before = source.stat().st_size // 1024
        after = target.stat().st_size // 1024
        print(f"  {target.relative_to(ROOT)}  {before} KB -> {after} KB")

    print(f"Shriftlar tayyor: {OUTPUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

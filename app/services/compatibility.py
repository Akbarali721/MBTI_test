"""Ikki xarakter tipining mosligini hisoblaydi.

Modul sof: bazaga ham, freymvorkka ham bog'liq emas. Matnlar bu yerda emas —
faqat i18n kalitlari qaytariladi, tarjima shablonda bo'ladi.

Model haqida ochiq bo'lish kerak: bu ilmiy o'lchov emas, balki to'rt o'lchov
bo'yicha o'xshashlik va to'ldiruvchanlikni izohlaydigan qoidalar to'plami.
Shuning uchun eng past ball ham 40 dan yuqori — hech bir juftlik "mos emas"
deb belgilanmaydi, faqat qayerda kuch, qayerda ishqalanish borligi ko'rsatiladi.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

DIMENSION_POLES: tuple[tuple[str, str], ...] = (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))
DIMENSION_KEYS: tuple[str, ...] = ("ei", "sn", "tf", "jp")

ALL_TYPES: tuple[str, ...] = tuple("".join(letters) for letters in itertools.product(*DIMENSION_POLES))

# (bir xil bo'lsa, farq qilsa) — S/N eng katta vaznga ega, chunki u odamlar bir-birini
# qanday tushunishini belgilaydi; T/F va E/I farqi ko'pincha to'ldiruvchi bo'ladi.
_WEIGHTS: dict[str, tuple[int, int]] = {
    "ei": (20, 14),
    "sn": (30, 8),
    "tf": (25, 14),
    "jp": (25, 10),
}

HIGH_BAND = 80
MEDIUM_BAND = 62


@dataclass(frozen=True)
class DimensionMatch:
    key: str
    left_letter: str
    right_letter: str
    same: bool
    #  i18n kaliti: bir xil bo'lsa qutb bo'yicha, farq qilsa umumiy izoh.
    text_key: str


@dataclass(frozen=True)
class Compatibility:
    left_type: str
    right_type: str
    score: int
    band: str
    dimensions: tuple[DimensionMatch, ...]
    strength_keys: tuple[str, ...]
    friction_keys: tuple[str, ...]
    advice_keys: tuple[str, ...]


def normalize_type(value: str | None) -> str | None:
    candidate = (value or "").strip().upper()
    return candidate if candidate in ALL_TYPES else None


def _band(score: int) -> str:
    if score >= HIGH_BAND:
        return "high"
    if score >= MEDIUM_BAND:
        return "medium"
    return "growing"


def _dimension_match(index: int, left: str, right: str) -> DimensionMatch:
    key = DIMENSION_KEYS[index]
    left_letter, right_letter = left[index], right[index]
    same = left_letter == right_letter
    suffix = f"same_{left_letter.lower()}" if same else "diff"
    return DimensionMatch(
        key=key,
        left_letter=left_letter,
        right_letter=right_letter,
        same=same,
        text_key=f"compat.{key}.{suffix}",
    )


def compare_types(left: str, right: str) -> Compatibility:
    left_type = normalize_type(left)
    right_type = normalize_type(right)
    if left_type is None or right_type is None:
        raise ValueError("Noma'lum xarakter tipi")

    matches = tuple(_dimension_match(index, left_type, right_type) for index in range(4))
    score = sum(_WEIGHTS[m.key][0 if m.same else 1] for m in matches)

    strengths = tuple(f"compat.strength.{m.key}_{'same' if m.same else 'diff'}" for m in matches if m.same)
    frictions = tuple(f"compat.friction.{m.key}" for m in matches if not m.same)
    advice = tuple(f"compat.advice.{m.key}" for m in matches if not m.same)

    # Hamma o'lchov mos kelgan juftlik uchun ham aytadigan gap bo'lishi kerak.
    if not frictions:
        advice = ("compat.advice.identical",)
    if not strengths:
        strengths = ("compat.strength.all_diff",)

    return Compatibility(
        left_type=left_type,
        right_type=right_type,
        score=score,
        band=_band(score),
        dimensions=matches,
        strength_keys=strengths,
        friction_keys=frictions,
        advice_keys=advice,
    )


def pair_slug(left: str, right: str) -> str:
    return f"{left.upper()}-{right.upper()}"


def parse_pair_slug(slug: str) -> tuple[str, str] | None:
    parts = (slug or "").upper().split("-")
    if len(parts) != 2:
        return None
    left, right = normalize_type(parts[0]), normalize_type(parts[1])
    if left is None or right is None:
        return None
    return left, right

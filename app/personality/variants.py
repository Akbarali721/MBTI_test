"""Savol to'plamlari o'rtasida A/B taqsimoti.

Taqsimot sozlamadan o'qiladi: "A" (bitta to'plam) yoki "A:70,B:30" (vaznli).
Tanlov sessiya yaratilganda bir marta qilinadi va sessiyada saqlanadi, shuning uchun
foydalanuvchi test davomida boshqa to'plamga o'tib ketmaydi.
"""

from __future__ import annotations

import random

from app.models.personality import DEFAULT_VARIANT

MAX_VARIANT_LENGTH = 8


def parse_spec(spec: str | None) -> list[tuple[str, int]]:
    """ "A:70,B:30" -> [("A", 70), ("B", 30)]. Yaroqsiz qism jimgina tashlab ketiladi."""
    entries: list[tuple[str, int]] = []
    for chunk in (spec or "").split(","):
        piece = chunk.strip()
        if not piece:
            continue
        name, _, weight_text = piece.partition(":")
        name = name.strip().upper()[:MAX_VARIANT_LENGTH]
        if not name.isalnum():
            continue
        try:
            weight = int(weight_text) if weight_text.strip() else 1
        except ValueError:
            continue
        if weight > 0:
            entries.append((name, weight))
    return entries or [(DEFAULT_VARIANT, 1)]


def choose_variant(spec: str | None, *, rng: random.Random | None = None) -> str:
    entries = parse_spec(spec)
    if len(entries) == 1:
        return entries[0][0]
    generator = rng or random
    names = [name for name, _ in entries]
    weights = [weight for _, weight in entries]
    return generator.choices(names, weights=weights, k=1)[0]


def known_variants(spec: str | None) -> list[str]:
    return [name for name, _ in parse_spec(spec)]


def normalize_variant(value: str | None) -> str:
    candidate = (value or "").strip().upper()[:MAX_VARIANT_LENGTH]
    return candidate if candidate.isalnum() else DEFAULT_VARIANT

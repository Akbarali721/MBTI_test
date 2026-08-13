"""Test analytics: intent va feedback qiymatlari hamda admin ko'rinishi."""

from __future__ import annotations

INTENT_VALUES: frozenset[str] = frozenset(
    {"strengths", "career", "self_understanding", "curiosity"}
)

FEEDBACK_RATING_VALUES: frozenset[str] = frozenset(
    {"very_accurate", "partly_accurate", "not_accurate"}
)

FEEDBACK_INTEREST_VALUES: frozenset[str] = frozenset(
    {"career", "strengths", "relationships", "stress", "confidence"}
)

DEFAULT_SOURCE = "direct"

INTENT_ADMIN_LABELS: dict[str, str] = {
    "strengths": "Kuchli tomonlar",
    "career": "Kasb/yo‘nalish",
    "self_understanding": "O‘zini tushunish",
    "curiosity": "Shunchaki qiziqish",
}

FEEDBACK_RATING_ADMIN_LABELS: dict[str, str] = {
    "very_accurate": "Juda mos",
    "partly_accurate": "Qisman mos",
    "not_accurate": "Unchalik mos emas",
}

FEEDBACK_INTEREST_ADMIN_LABELS: dict[str, str] = {
    "career": "Kasb va ish yo‘nalishi",
    "strengths": "Kuchli va zaif tomonlar",
    "relationships": "Munosabatlar",
    "stress": "Stress paytida",
    "confidence": "O‘ziga ishonch",
}


def intent_admin_label(code: str | None) -> str:
    if not code:
        return "—"
    return INTENT_ADMIN_LABELS.get(code, code)


def feedback_rating_admin_label(code: str | None) -> str:
    if not code:
        return "—"
    return FEEDBACK_RATING_ADMIN_LABELS.get(code, code)


def feedback_interest_admin_label(code: str | None) -> str:
    if not code:
        return "—"
    return FEEDBACK_INTEREST_ADMIN_LABELS.get(code, code)

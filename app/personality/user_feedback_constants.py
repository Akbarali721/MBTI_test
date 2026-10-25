"""Natija sahifasidagi foydalanuvchi fikri (positive / partial / negative)."""

from __future__ import annotations

USER_FEEDBACK_RATING_VALUES: frozenset[str] = frozenset({"positive", "partial", "negative"})

USER_FEEDBACK_MAX_COMMENT_LEN = 2000

USER_FEEDBACK_ADMIN_LABELS: dict[str, str] = {
    "positive": "👍 Juda mos",
    "partial": "🤔 Qisman mos",
    "negative": "👎 Mos kelmadi",
}


def user_feedback_admin_label(code: str | None) -> str:
    if not code:
        return "—"
    return USER_FEEDBACK_ADMIN_LABELS.get(code, code)

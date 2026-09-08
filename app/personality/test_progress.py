"""Test progress: max savol va holat yordamchilari."""

from __future__ import annotations

from datetime import timedelta

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.personality.constants import SESSION_QUESTION_COUNT
from app.timeutils import as_utc, utcnow

# Oxirgi faollikdan keyin sessiya "tashlab ketilgan" deb hisoblanadi.
ABANDONED_AFTER = timedelta(days=7)


def question_number_from_index(question_index: int) -> int:
    """0-based indeks → 1-based savol raqami."""
    return max(1, question_index + 1)


def apply_question_reached(session: PersonalityTestSession, question_index: int) -> None:
    """Eng uzoq yetilgan savolni faqat oshirish yo'nalishida yangilaydi."""
    reached = question_number_from_index(question_index)
    if reached > session.max_question_reached:
        session.max_question_reached = reached


def progress_reached(session: PersonalityTestSession) -> int:
    total = session.total_questions or SESSION_QUESTION_COUNT
    if session.status == PersonalitySessionStatus.COMPLETED:
        return total
    return max(session.max_question_reached, session.answered_questions, 0)


def progress_total(session: PersonalityTestSession) -> int:
    return session.total_questions or SESSION_QUESTION_COUNT


def progress_percent(session: PersonalityTestSession) -> float:
    total = progress_total(session)
    if total <= 0:
        return 0.0
    return round(progress_reached(session) / total * 100, 1)


def progress_status_label(session: PersonalityTestSession | None) -> str:
    if session is None or session.started_at is None:
        return "—"
    if session.status == PersonalitySessionStatus.COMPLETED:
        return "Tugatgan"
    last = session.last_activity_at or session.last_answered_at or session.started_at
    if last is not None and utcnow() - as_utc(last) > ABANDONED_AFTER:
        return "Tashlab ketgan"
    return "Davom etmoqda"

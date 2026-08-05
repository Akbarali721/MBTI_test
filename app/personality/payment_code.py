from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.personality import PersonalityTestSession

PAYMENT_CODE_MIN_LENGTH = 8


def payment_code_for_session(db: Session, session: PersonalityTestSession) -> str:
    token = session.token.lower()
    for length in range(PAYMENT_CODE_MIN_LENGTH, len(token) + 1):
        prefix = token[:length]
        count = db.scalar(
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(PersonalityTestSession.token.like(f"{prefix}%"))
        )
        if count == 1:
            return prefix
    return token


def find_sessions_by_payment_code(db: Session, code: str, *, limit: int = 50) -> list[PersonalityTestSession]:
    normalized = code.strip().lower()
    if not normalized:
        return []
    stmt = (
        select(PersonalityTestSession)
        .where(PersonalityTestSession.token.like(f"{normalized}%"))
        .order_by(PersonalityTestSession.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())

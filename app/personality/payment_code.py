from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.personality import PersonalityTestSession

PAYMENT_CODE_MIN_LENGTH = 8
PAYMENT_CODE_MAX_LENGTH = 16


def generate_payment_code(db: Session, token: str) -> str:
    """Tokendan qisqa noyob kod: bitta so'rov bilan band prefikslar tekshiriladi."""
    normalized = (token or "").strip().lower()
    if not normalized:
        return ""
    shortest = normalized[:PAYMENT_CODE_MIN_LENGTH]
    longest = min(len(normalized), PAYMENT_CODE_MAX_LENGTH)

    taken = set(
        db.scalars(
            select(PersonalityTestSession.payment_code).where(
                PersonalityTestSession.payment_code.startswith(shortest, autoescape=True)
            )
        ).all()
    )
    for length in range(PAYMENT_CODE_MIN_LENGTH, longest + 1):
        candidate = normalized[:length]
        if candidate not in taken:
            return candidate
    return normalized[:PAYMENT_CODE_MAX_LENGTH]


def payment_code_for_session(db: Session, session: PersonalityTestSession) -> str:
    """Sessiyaning doimiy to'lov kodi; eski qatorlar uchun bir marta hosil qilinadi."""
    if session.payment_code:
        return session.payment_code
    code = generate_payment_code(db, session.token)
    session.payment_code = code
    db.flush()
    return code


def find_sessions_by_payment_code(db: Session, code: str, *, limit: int = 50) -> list[PersonalityTestSession]:
    normalized = code.strip().lower()
    if not normalized:
        return []
    stmt = (
        select(PersonalityTestSession)
        .where(PersonalityTestSession.payment_code == normalized)
        .order_by(PersonalityTestSession.created_at.desc())
        .limit(limit)
    )
    found = list(db.scalars(stmt).all())
    if found:
        return found
    if len(normalized) >= PAYMENT_CODE_MIN_LENGTH and normalized.isalnum():
        prefix_stmt = (
            select(PersonalityTestSession)
            .where(PersonalityTestSession.token.startswith(normalized, autoescape=True))
            .order_by(PersonalityTestSession.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(prefix_stmt).all())
    return []

"""Natijani ommaviy ulashish uchun kod.

Sessiya tokeni — natijaga to'liq kirish huquqi (premium bo'limlar, to'lov oqimi).
Shuning uchun ulashish havolasi undan hosil qilinmaydi: mustaqil tasodifiy kod
faqat anonim ko'rinishni ochadi va oshkor bo'lsa ham hech narsa yo'qotilmaydi.
"""

import secrets
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession

SHARE_CODE_BYTES = 8
_MAX_ATTEMPTS = 5


def share_path(share_code: str) -> str:
    return f"/r/{share_code}"


def og_image_path(result_type: str) -> str:
    return f"/static/images/og/{result_type.upper()}.png"


def telegram_share_url(share_url: str, text: str) -> str:
    return "https://t.me/share/url?" + urlencode({"url": share_url, "text": text})


def _candidate() -> str:
    return secrets.token_urlsafe(SHARE_CODE_BYTES)


def generate_share_code(db: Session) -> str:
    for _ in range(_MAX_ATTEMPTS):
        code = _candidate()
        taken = db.scalar(select(PersonalityTestSession.id).where(PersonalityTestSession.share_code == code))
        if taken is None:
            return code
    # Bunga yetib kelish amalda imkonsiz; baribir jimgina takror qaytarmaymiz.
    return secrets.token_urlsafe(SHARE_CODE_BYTES * 2)


def share_code_for_session(db: Session, session: PersonalityTestSession) -> str:
    """Sessiyaning doimiy ulashish kodi; eski qatorlar uchun bir marta hosil qilinadi."""
    if session.share_code:
        return session.share_code
    code = generate_share_code(db)
    session.share_code = code
    db.flush()
    return code


def find_shared_session(db: Session, share_code: str) -> PersonalityTestSession | None:
    """Faqat tugallangan sessiya ulashilishi mumkin."""
    normalized = (share_code or "").strip()
    if not normalized:
        return None
    stmt = select(PersonalityTestSession).where(
        PersonalityTestSession.share_code == normalized,
        PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
    )
    session = db.scalar(stmt)
    if session is None or not session.result_type:
        return None
    return session

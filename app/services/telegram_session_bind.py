"""Telegram WebApp foydalanuvchisini MBTI sessiyasiga bog'lash."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.models.personality import PersonalityTestSession
from app.telegram.webapp_auth import TelegramWebAppUser, parse_webapp_user


def bind_telegram_user_to_session(
    db: Session,
    session: PersonalityTestSession,
    user: TelegramWebAppUser,
) -> PersonalityTestSession:
    """Sessiyaga Telegram ID/username yozadi (mavjud qiymat ustiga yozilmaydi)."""
    if session.telegram_user_id is None:
        session.telegram_user_id = user.id
    if user.username and not session.telegram_username:
        session.telegram_username = user.username[:64]
    if user.first_name and not session.telegram_first_name:
        session.telegram_first_name = user.first_name[:128]
    db.flush()
    db.refresh(session)
    return session


def bind_session_from_webapp_init_data(
    db: Session,
    session: PersonalityTestSession,
    init_data: str,
) -> PersonalityTestSession | None:
    user = parse_webapp_user(init_data, settings.bot_token)
    if user is None:
        return None
    return bind_telegram_user_to_session(db, session, user)

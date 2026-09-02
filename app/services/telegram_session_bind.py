"""Telegram WebApp foydalanuvchisini MBTI sessiyasiga bog'lash."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.models.personality import PersonalityTestSession
from app.services.telegram_referral_service import sync_referral_to_session
from app.services.telegram_user_service import (
    TelegramProfileInput,
    sync_session_telegram_fields,
    upsert_from_webapp,
)
from app.telegram.webapp_auth import TelegramWebAppUser, parse_webapp_user


def bind_telegram_user_to_session(
    db: Session,
    session: PersonalityTestSession,
    user: TelegramWebAppUser,
) -> PersonalityTestSession:
    """Sessiyaga Telegram ID/username yozadi va profil jadvalini yangilaydi."""
    tg_user = upsert_from_webapp(
        db,
        TelegramProfileInput(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        ),
    )
    sync_session_telegram_fields(session, tg_user)
    sync_referral_to_session(db, tg_user=tg_user, session=session)
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

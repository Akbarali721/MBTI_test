"""Telegram bot orqali kelgan referallar (ref_<telegram_id>)."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramReferral, TelegramUser
from app.services import telegram_user_service as tg_users
from app.services.referral_service import may_attribute
from app.timeutils import utcnow

logger = logging.getLogger(__name__)

REF_PREFIX = "ref_"


def parse_referral_telegram_id(start_arg: str | None) -> int | None:
    if not start_arg:
        return None
    cleaned = start_arg.strip()
    if not cleaned.lower().startswith(REF_PREFIX):
        return None
    raw_id = cleaned[len(REF_PREFIX) :]
    try:
        telegram_id = int(raw_id)
    except ValueError:
        return None
    if telegram_id <= 0:
        return None
    return telegram_id


def telegram_referral_url(telegram_id: int) -> str:
    bot = (settings.telegram_bot_username or settings.bot_username or "XarakterimBot").lstrip("@")
    return f"https://t.me/{bot}?start={REF_PREFIX}{telegram_id}"


def attribute_bot_referral(
    db: Session,
    *,
    referred: TelegramUser,
    referrer_telegram_id: int,
    now: datetime | None = None,
) -> bool:
    """Bot /start ref_<id>: munosabatni saqlash."""
    if not settings.referral_enabled:
        return False
    if referred.telegram_id == referrer_telegram_id:
        return False

    existing = tg_users.get_referral_for_referred(db, referred.id)
    if existing is not None:
        return False

    if tg_users.has_completed_test(db, referred.telegram_id):
        return False

    referrer = tg_users.get_by_telegram_id(db, referrer_telegram_id)
    if referrer is None:
        return False

    moment = now or utcnow()
    db.add(
        TelegramReferral(
            referrer_telegram_user_id=referrer.id,
            referred_telegram_user_id=referred.id,
            created_at=moment,
        )
    )
    db.flush()
    logger.info(
        "Telegram referal biriktirildi: referrer=%s referred=%s",
        referrer_telegram_id,
        referred.telegram_id,
    )
    return True


def sync_referral_to_session(
    db: Session,
    *,
    tg_user: TelegramUser,
    session: PersonalityTestSession,
) -> bool:
    """Telegram referalini sessiyaga o'tkazish (WebApp ochilganda)."""
    if not may_attribute(session):
        return False

    referral = tg_users.get_referral_for_referred(db, tg_user.id)
    if referral is None:
        return False

    referrer_tg = db.get(TelegramUser, referral.referrer_telegram_user_id)
    if referrer_tg is None:
        return False
    if referrer_tg.telegram_id == tg_user.telegram_id:
        return False

    referrer_session = tg_users.primary_session_for_telegram_user(db, referrer_tg.telegram_id)
    if referrer_session is None:
        return False
    if referrer_session.id == session.id:
        return False

    session.referred_by_session_id = referrer_session.id
    db.flush()
    return True


def mark_referral_completed(
    db: Session,
    completed_session: PersonalityTestSession,
    *,
    now: datetime | None = None,
) -> None:
    """Test tugaganda Telegram referalini completed deb belgilash."""
    telegram_id = completed_session.telegram_user_id
    if telegram_id is None:
        return

    tg_user = tg_users.get_by_telegram_id(db, telegram_id)
    if tg_user is None:
        return

    referral = tg_users.get_referral_for_referred(db, tg_user.id)
    if referral is None:
        return
    if referral.completed_at is not None:
        return
    if completed_session.status != PersonalitySessionStatus.COMPLETED:
        return

    moment = now or utcnow()
    referral.completed_at = moment
    referral.referred_session_id = completed_session.id
    db.flush()


def set_referral_premium_source(db: Session, referrer_session: PersonalityTestSession) -> None:
    """Mukofot berilganda premium_source = referral."""
    telegram_id = referrer_session.telegram_user_id
    if telegram_id is None:
        return
    tg_user = tg_users.get_by_telegram_id(db, telegram_id)
    if tg_user is not None and not tg_user.premium_source:
        tg_user.premium_source = "referral"
    if not referrer_session.premium_source:
        referrer_session.premium_source = "referral"
    db.flush()

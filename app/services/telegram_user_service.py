"""Telegram foydalanuvchi profili — bot va WebApp uchun umumiy xizmat."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramReferral, TelegramUser
from app.timeutils import utcnow


@dataclass(frozen=True)
class TelegramProfileInput:
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


def get_by_telegram_id(db: Session, telegram_id: int) -> TelegramUser | None:
    return db.scalar(select(TelegramUser).where(TelegramUser.telegram_id == telegram_id))


def upsert_from_bot_start(
    db: Session,
    profile: TelegramProfileInput,
    *,
    now: datetime | None = None,
) -> TelegramUser:
    """Bot /start: yaratish yoki yangilash, bot_started_at saqlash."""
    moment = now or utcnow()
    user = get_by_telegram_id(db, profile.telegram_id)
    if user is None:
        user = TelegramUser(
            telegram_id=profile.telegram_id,
            bot_started_at=moment,
        )
        db.add(user)
    elif user.bot_started_at is None:
        user.bot_started_at = moment

    _apply_profile_fields(user, profile)
    user.updated_at = moment
    db.flush()
    return user


def upsert_from_webapp(
    db: Session,
    profile: TelegramProfileInput,
    *,
    now: datetime | None = None,
) -> TelegramUser:
    """WebApp initData: profilni yangilash (bot_started_at o'zgarmaydi)."""
    moment = now or utcnow()
    user = get_by_telegram_id(db, profile.telegram_id)
    if user is None:
        user = TelegramUser(telegram_id=profile.telegram_id)
        db.add(user)

    _apply_profile_fields(user, profile)
    user.updated_at = moment
    db.flush()
    return user


def save_phone_number(
    db: Session,
    *,
    telegram_id: int,
    phone_number: str,
    now: datetime | None = None,
) -> TelegramUser | None:
    user = get_by_telegram_id(db, telegram_id)
    if user is None:
        return None
    moment = now or utcnow()
    user.phone_number = phone_number[:32]
    user.phone_shared_at = moment
    user.updated_at = moment
    db.flush()
    return user


def _apply_profile_fields(user: TelegramUser, profile: TelegramProfileInput) -> None:
    if profile.username is not None:
        user.telegram_username = profile.username[:64] if profile.username else None
    if profile.first_name is not None:
        user.telegram_first_name = profile.first_name[:128] if profile.first_name else None
    if profile.last_name is not None:
        user.telegram_last_name = profile.last_name[:128] if profile.last_name else None


def has_completed_test(db: Session, telegram_id: int) -> bool:
    stmt = (
        select(PersonalityTestSession.id)
        .where(
            PersonalityTestSession.telegram_user_id == telegram_id,
            PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def primary_session_for_telegram_user(db: Session, telegram_id: int) -> PersonalityTestSession | None:
    """Referrer sessiyasi: avval tugatilgan, keyin eng so'nggi."""
    completed = db.scalar(
        select(PersonalityTestSession)
        .where(
            PersonalityTestSession.telegram_user_id == telegram_id,
            PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
        )
        .order_by(PersonalityTestSession.completed_at.desc())
        .limit(1)
    )
    if completed is not None:
        return completed
    return db.scalar(
        select(PersonalityTestSession)
        .where(PersonalityTestSession.telegram_user_id == telegram_id)
        .order_by(PersonalityTestSession.created_at.desc())
        .limit(1)
    )


def sync_session_telegram_fields(
    session: PersonalityTestSession,
    tg_user: TelegramUser,
) -> None:
    if session.telegram_user_id is None:
        session.telegram_user_id = tg_user.telegram_id
    if tg_user.telegram_username and not session.telegram_username:
        session.telegram_username = tg_user.telegram_username
    if tg_user.telegram_first_name and not session.telegram_first_name:
        session.telegram_first_name = tg_user.telegram_first_name
    if tg_user.telegram_last_name and not session.telegram_last_name:
        session.telegram_last_name = tg_user.telegram_last_name


def get_referral_for_referred(db: Session, referred_telegram_user_id: int) -> TelegramReferral | None:
    return db.scalar(
        select(TelegramReferral).where(
            TelegramReferral.referred_telegram_user_id == referred_telegram_user_id
        )
    )


def list_referrals_for_referrer(db: Session, referrer_telegram_user_id: int) -> list[TelegramReferral]:
    stmt = (
        select(TelegramReferral)
        .where(TelegramReferral.referrer_telegram_user_id == referrer_telegram_user_id)
        .order_by(TelegramReferral.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def completed_telegram_referral_count(db: Session, referrer_telegram_user_id: int) -> int:
    stmt = (
        select(TelegramReferral)
        .where(
            TelegramReferral.referrer_telegram_user_id == referrer_telegram_user_id,
            TelegramReferral.completed_at.is_not(None),
        )
    )
    return len(list(db.scalars(stmt).all()))

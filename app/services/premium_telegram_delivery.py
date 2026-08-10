"""Premium tasdiqlangach Telegram xabarini yuborish (navbat + admin sinxron urinish)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from app.bot.outbox_worker import deliver_one
from app.config import settings
from app.models.enums import NOTIFICATION_TERMINAL_STATUSES, NotificationStatus
from app.models.notification import NotificationOutbox
from app.models.personality import PersonalityTestSession
from app.services.notification_outbox import USER_APPROVED

logger = logging.getLogger(__name__)


def resolve_premium_chat_id(session: PersonalityTestSession, payment_telegram_id: int | None) -> int | None:
    if session.telegram_user_id:
        return session.telegram_user_id
    if payment_telegram_id:
        return payment_telegram_id
    return None


def latest_user_approved_outbox_row(db: Session, session_id: int) -> NotificationOutbox | None:
    stmt = (
        select(NotificationOutbox)
        .where(NotificationOutbox.kind == USER_APPROVED)
        .order_by(desc(NotificationOutbox.id))
        .limit(20)
    )
    for row in db.scalars(stmt):
        params = row.params if isinstance(row.params, dict) else {}
        if params.get("session_id") == session_id:
            return row
    return None


def try_deliver_premium_approved_message(
    db: Session,
    *,
    session_id: int,
    session_factory: sessionmaker | None = None,
) -> str | None:
    """Navbatdagi USER_APPROVED xabarini darhol yuborishga urinadi.

    Premium allaqachon saqlangan bo'lishi kerak. Xato bo'lsa matn qaytariladi (ogohlantirish).
    """
    if not (settings.bot_token or "").strip():
        return "BOT_TOKEN sozlanmagan — Telegram xabari yuborilmadi."

    row = latest_user_approved_outbox_row(db, session_id)
    if row is None:
        return "Telegram xabari navbatga qo‘yilmagan (foydalanuvchi bog‘lanmagan bo‘lishi mumkin)."

    if row.status in NOTIFICATION_TERMINAL_STATUSES:
        return None

    from aiogram import Bot

    from app.database import SessionLocal

    factory = session_factory or SessionLocal
    bot = Bot(token=settings.bot_token)

    async def _run() -> str:
        try:
            status = await deliver_one(bot, factory, row.id)
        finally:
            await bot.session.close()
        if status == NotificationStatus.SENT.value:
            return ""
        if status in (NotificationStatus.BLOCKED.value, NotificationStatus.FAILED.value):
            return "Telegram xabari yuborilmadi."
        if status == "retry":
            return "Telegram xabari hozircha yuborilmadi — navbat keyinroq qayta urinadi."
        return "Telegram xabari yuborilmadi."

    try:
        warning = asyncio.run(_run())
    except Exception:
        logger.exception("Premium Telegram xabarini sinxron yuborib bo‘lmadi (sessiya %s)", session_id)
        return "Telegram xabari yuborilmadi."
    return warning or None

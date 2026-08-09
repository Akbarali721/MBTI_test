"""Bildirishnoma navbatini yetkazuvchi ishchi.

Bot jarayonida ishlaydi (veb jarayonida Bot obyekti yo'q va uvicorn bir nechta
ishchi bilan ishga tushsa navbat bir necha marta yuborilardi).

Muhim tafsilotlar:

* Har qator yuborishdan OLDIN bazadagi holatni qayta o'qiydi. Admin avval rad etib,
  keyin tasdiqlagan bo'lsa, "rad etildi" xabari endi yolg'on — u yuborilmaydi,
  balki `cancelled` qilinadi. Bu navbat tartibini kafolatlashdan ko'ra ishonchli.
* Xato turlari ajratiladi. Foydalanuvchi botni bloklagan bo'lsa qayta urinishning
  ma'nosi yo'q; tarmoq uzilgan bo'lsa — bor. Noto'g'ri BOT_TOKEN esa BUTUN navbatni
  "failed" qilib yuborishi mumkin edi, shuning uchun u qator xatosi emas, jarayon
  xatosi deb qaraladi va hech bir qatorga tegilmaydi.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramConflictError,
    TelegramEntityTooLarge,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNetworkError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.types import BufferedInputFile
from sqlalchemy.orm import Session, sessionmaker

from app.bot import messages
from app.bot.messages import Message, Outcome
from app.config import settings
from app.database import SessionLocal
from app.models.enums import NotificationStatus
from app.models.notification import OUTBOX_WORKER_HEARTBEAT, NotificationOutbox
from app.services import notification_outbox as outbox
from app.services.notification_outbox import (
    ADMIN_RECEIPT,
    KNOWN_KINDS,
    PREMIUM_PDF,
    REFERRAL_REWARD,
    SCHEMA_VERSION,
    USER_APPROVED,
    USER_REJECTED,
)

logger = logging.getLogger(__name__)

# Noma'lum tur yoki kelajakdagi sxema: qator terminal QILINMAYDI, shunchaki uzoqqa
# suriladi. Deployʼni orqaga qaytarish navbatni yo'q qilmasligi kerak.
UNSUPPORTED_DELAY_SECONDS = 3600
# Jarayon darajasidagi xato (token noto'g'ri, ikkinchi bot ishlayapti) — pauza.
CIRCUIT_BREAK_SECONDS = 60


class ProcessLevelError(Exception):
    """Qatorga emas, butun jarayonga tegishli xato."""


def worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"[:64]


def _session_scope(factory: sessionmaker) -> Session:
    return factory()


# --- Xabar qurish ---


def build_message(db: Session, row: NotificationOutbox) -> Message | Outcome:
    """Yuboriladigan xabarni QAYTA quradi va holatni tekshiradi.

    `Outcome` qaytsa — xabar yuborilmaydi (bekor qilingan yoki nuqsonli).
    """
    if row.kind not in KNOWN_KINDS or row.schema_version > SCHEMA_VERSION:
        return Outcome(error=f"qo‘llab-quvvatlanmaydigan tur: {row.kind} v{row.schema_version}")

    params = row.params if isinstance(row.params, dict) else {}
    try:
        if row.kind == ADMIN_RECEIPT:
            return messages.admin_receipt_message(db, int(params["payment_id"]))
        if row.kind == USER_APPROVED:
            return messages.user_approved_message(db, int(params["session_id"]))
        if row.kind == USER_REJECTED:
            return messages.user_rejected_message(db, int(params["payment_id"]))
        if row.kind == PREMIUM_PDF:
            return messages.premium_pdf_message(db, int(params["session_id"]))
        if row.kind == REFERRAL_REWARD:
            return messages.referral_reward_message(db, int(params["session_id"]), int(params["days"]))
    except (KeyError, TypeError, ValueError) as exc:
        return Outcome(status=NotificationStatus.INVALID.value, error=f"params nuqsoni: {exc}")
    return Outcome(status=NotificationStatus.INVALID.value, error="noma'lum tur")


async def _send(bot: Bot, chat_id: int, message: Message) -> None:
    if message.document_bytes is not None:
        await bot.send_document(
            chat_id,
            BufferedInputFile(message.document_bytes, filename=message.document_name or "hisobot.pdf"),
            caption=message.caption,
        )
        return
    if message.photo_file_id:
        await bot.send_photo(
            chat_id, message.photo_file_id, caption=message.caption, reply_markup=message.keyboard
        )
        return
    if message.document_file_id:
        await bot.send_document(
            chat_id, message.document_file_id, caption=message.caption, reply_markup=message.keyboard
        )
        return
    await bot.send_message(chat_id, message.text or message.caption or "", reply_markup=message.keyboard)


async def deliver_one(bot: Bot, factory: sessionmaker, row_id: int) -> str:
    """Bitta qatorni yetkazadi va natijasini yozadi. Qaytadigan qiymat — yakuniy holat."""
    db = _session_scope(factory)
    try:
        row = outbox.get_row(db, row_id)
        if row is None:
            return "missing"
        chat_id = row.chat_id
        built = await asyncio.to_thread(build_message, db, row)
        # Xabar qurishda yaratilgan qiymatlar (masalan ulashish kodi) saqlanishi kerak.
        db.commit()
    except asyncio.CancelledError:
        db.rollback()
        raise
    except Exception as exc:
        # Xabarni qurishda KUTILMAGAN xato (natija kontenti yo'q, PDF yig'ilmadi,
        # baza uzildi). Bu istisno chiqib ketsa qator "sending" holatida qolib,
        # ijara tugagunga qadar butun paket bilan birga to'xtab turardi.
        db.rollback()
        logger.exception("Bildirishnomani qurib bo‘lmadi: #%s", row_id)
        return _record_outcome(factory, row_id, Outcome(error=f"qurish xatosi: {exc}"))
    finally:
        db.close()

    if isinstance(built, Outcome):
        return _record_outcome(factory, row_id, built)

    outcome = await _attempt(bot, chat_id, built)
    return _record_outcome(factory, row_id, outcome)


async def _attempt(bot: Bot, chat_id: int, message: Message) -> Outcome:
    try:
        await _send(bot, chat_id, message)
        return Outcome(status=NotificationStatus.SENT.value)
    except (TelegramUnauthorizedError, TelegramConflictError) as exc:
        # Bu qatorning muammosi emas: token noto'g'ri yoki ikkinchi nusxa ishlayapti.
        # Qatorlarni "failed" qilib butun navbatni kuydirmaymiz.
        raise ProcessLevelError(str(exc)) from exc
    except TelegramRetryAfter as exc:
        return Outcome(retry_after=float(exc.retry_after), refund_attempt=True, error="flood limit")
    except TelegramMigrateToChat as exc:
        return Outcome(retry_after=1.0, refund_attempt=True, error=f"chat ko‘chdi: {exc}")
    except TelegramForbiddenError:
        return Outcome(status=NotificationStatus.BLOCKED.value, error="foydalanuvchi botni bloklagan")
    except (TelegramNotFound, TelegramEntityTooLarge) as exc:
        return Outcome(status=NotificationStatus.FAILED.value, error=str(exc))
    except TelegramBadRequest as exc:
        if message.photo_file_id or message.document_file_id:
            # Eskirgan file_id uchun rasmsiz xabar ham sotuvni saqlab qoladi.
            fallback = Message(text=message.caption or message.text, keyboard=message.keyboard)
            try:
                await _send(bot, chat_id, fallback)
                return Outcome(status=NotificationStatus.SENT.value, error=f"faylsiz yuborildi: {exc}")
            except Exception as inner:
                return Outcome(status=NotificationStatus.FAILED.value, error=str(inner))
        return Outcome(status=NotificationStatus.FAILED.value, error=str(exc))
    except (TelegramNetworkError, TelegramServerError) as exc:
        return Outcome(error=str(exc))
    except Exception as exc:
        logger.exception("Bildirishnoma yuborishda kutilmagan xato")
        return Outcome(error=str(exc))


def _record_outcome(factory: sessionmaker, row_id: int, outcome: Outcome) -> str:
    db = _session_scope(factory)
    try:
        if outcome.status:
            outbox.mark_terminal(db, row_id, outcome.status, error=outcome.error)
            return outcome.status
        if outcome.retry_after is not None:
            outbox.schedule_retry(
                db,
                row_id,
                delay_seconds=outcome.retry_after,
                error=outcome.error,
                refund_attempt=outcome.refund_attempt,
            )
            return "retry"
        row = outbox.get_row(db, row_id)
        if row is None:
            return "missing"
        delay = (
            UNSUPPORTED_DELAY_SECONDS
            if outcome.error and "qo‘llab-quvvatlanmaydigan" in outcome.error
            else outbox.backoff_delay(row.attempts)
        )
        outbox.schedule_retry(db, row_id, delay_seconds=delay, error=outcome.error)
        return "retry"
    finally:
        db.close()


async def drain_once(bot: Bot, factory: sessionmaker = SessionLocal, *, limit: int | None = None) -> int:
    """Navbatdan bir marta o'tadi va yuborilgan qatorlar sonini qaytaradi."""
    identity = worker_id()
    db = _session_scope(factory)
    try:
        outbox.reclaim_stale(db)
        claimed = outbox.claim_batch(db, worker_id=identity, limit=limit or settings.outbox_batch_size)
        outbox.touch_heartbeat(db, OUTBOX_WORKER_HEARTBEAT, detail=identity)
    finally:
        db.close()

    processed = 0
    for row_id in claimed:
        try:
            await deliver_one(bot, factory, row_id)
            processed += 1
        except asyncio.CancelledError:
            # To'xtatilganda qator "sending" da qolmasin — u qayta navbatga qaytadi.
            _release(factory, identity)
            raise
        except ProcessLevelError:
            _release(factory, identity)
            raise
        except Exception as exc:
            # Bitta yomon qator paketning qolganini tashlab ketmasligi kerak.
            logger.exception("Bildirishnoma #%s yetkazilmadi", row_id)
            _record_outcome(factory, row_id, Outcome(error=f"kutilmagan xato: {exc}"))
    return processed


def _release(factory: sessionmaker, identity: str) -> None:
    db = _session_scope(factory)
    try:
        outbox.release_all_claimed(db, identity)
    finally:
        db.close()


async def run_worker(bot: Bot, factory: sessionmaker = SessionLocal) -> None:
    """Cheksiz sikl — `run_bot()` ichida polling bilan yonma-yon ishlaydi."""
    logger.info("Bildirishnoma navbati ishchisi ishga tushdi (%s)", worker_id())
    while True:
        try:
            sent = await drain_once(bot, factory)
        except asyncio.CancelledError:
            logger.info("Bildirishnoma ishchisi to‘xtatildi")
            raise
        except ProcessLevelError as exc:
            logger.error("Telegram jarayon darajasidagi xato, pauza: %s", exc)
            await asyncio.sleep(CIRCUIT_BREAK_SECONDS)
            continue
        except Exception:
            logger.exception("Bildirishnoma ishchisida kutilmagan xato")
            await asyncio.sleep(settings.outbox_poll_seconds)
            continue
        if not sent:
            await asyncio.sleep(settings.outbox_poll_seconds)

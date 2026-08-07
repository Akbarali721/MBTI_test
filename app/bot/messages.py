"""Navbatdagi qatorlardan haqiqiy xabarni yig'ish.

Har bir quruvchi bazadagi HOZIRGI holatni qayta o'qiydi va xabar endi to'g'ri
bo'lmasa uni bekor qiladi. Sabab: navbat "kamida bir marta" yetkazadi va tartib
kafolatlanmaydi — admin avval rad etib, keyin tasdiqlasa, kechikkan "rad etildi"
xabari mijozga yolg'on gapirardi.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.orm import Session

from app.bot.keyboards import admin_receipt_keyboard, premium_result_keyboard
from app.config import settings
from app.models.enums import NotificationStatus
from app.models.payment_request import (
    ACTIVE_PAYMENT_STATUSES,
    PAYMENT_STATUS_REJECTED,
    PaymentRequest,
)
from app.models.personality import PersonalityTestSession
from app.pdf import pdf_filename
from app.services.premium_access import has_trial_premium, trial_days_left
from app.services.premium_payment_service import format_price_uzs
from app.services.result_pdf import PdfFontsUnavailable, PdfNotPremium, build_pdf_bytes

logger = logging.getLogger(__name__)

APPROVED_TEXT = "✅ To‘lov tasdiqlandi!\n\nPremium MBTI tahlilingiz ochildi."
REJECTED_TEXT = (
    "❌ To‘lovni tasdiqlab bo‘lmadi.\n\nIltimos, to‘g‘ri chekni qayta yuboring yoki admin bilan bog‘laning."
)
PDF_CAPTION = "📄 Premium tahlilingiz PDF sifatida."
REFERRAL_REWARD_TEXT = (
    "🎁 Do‘stlaringiz testni tugatdi — premium tahlil {days} kunga ochildi!\n\n"
    "Muddati: yana {left} kun. Yana do‘st taklif qilsangiz muddat uzayadi."
)


@dataclass(frozen=True)
class Message:
    text: str | None = None
    keyboard: InlineKeyboardMarkup | None = None
    photo_file_id: str | None = None
    document_file_id: str | None = None
    document_bytes: bytes | None = None
    document_name: str | None = None
    caption: str | None = None


@dataclass(frozen=True)
class Outcome:
    status: str | None = None
    error: str | None = None
    retry_after: float | None = None
    refund_attempt: bool = False


def _cancelled(reason: str) -> Outcome:
    return Outcome(status=NotificationStatus.CANCELLED.value, error=reason)


def payment_caption(payment: PaymentRequest, session: PersonalityTestSession) -> str:
    username = f"@{payment.telegram_username}" if payment.telegram_username else "—"
    return (
        "Yangi premium chek\n\n"
        f"Payment ID: {payment.id}\n"
        f"User: {payment.telegram_first_name or '—'}\n"
        f"Username: {username}\n"
        f"Telegram ID: {payment.telegram_user_id or '—'}\n"
        f"Session ID: {session.id}\n"
        f"Test kodi: {session.payment_code or '—'}\n"
        f"MBTI: {session.result_type or '—'}\n"
        f"Amount: {format_price_uzs(payment.amount)} so‘m"
    )


def admin_receipt_message(db: Session, payment_id: int) -> Message | Outcome:
    payment = db.get(PaymentRequest, payment_id)
    if payment is None or payment.session is None:
        return _cancelled("to‘lov topilmadi")
    if payment.status not in ACTIVE_PAYMENT_STATUSES:
        # Boshqa admin allaqachon hal qilgan.
        return _cancelled(f"to‘lov holati: {payment.status}")

    caption = payment_caption(payment, payment.session)
    keyboard = admin_receipt_keyboard(payment.id)
    if payment.receipt_type == "photo" and payment.receipt_file_id:
        return Message(photo_file_id=payment.receipt_file_id, caption=caption, keyboard=keyboard)
    if payment.receipt_type == "document" and payment.receipt_file_id:
        return Message(document_file_id=payment.receipt_file_id, caption=caption, keyboard=keyboard)
    return Message(text=caption, keyboard=keyboard)


def user_approved_message(db: Session, session_id: int) -> Message | Outcome:
    session = db.get(PersonalityTestSession, session_id)
    if session is None:
        return _cancelled("sessiya topilmadi")
    if not session.is_premium:
        return _cancelled("premium bekor qilingan")
    return Message(text=APPROVED_TEXT, keyboard=premium_result_keyboard(session.token))


def user_rejected_message(db: Session, payment_id: int) -> Message | Outcome:
    payment = db.get(PaymentRequest, payment_id)
    if payment is None or payment.session is None:
        return _cancelled("to‘lov topilmadi")
    if payment.status != PAYMENT_STATUS_REJECTED or payment.session.is_premium:
        # Rad etilgandan keyin tasdiqlangan bo'lsa, bu xabar endi yolg'on.
        return _cancelled("to‘lov endi rad etilgan holatda emas")
    return Message(text=REJECTED_TEXT)


def referral_reward_message(db: Session, session_id: int, days: int) -> Message | Outcome:
    """Referal mukofoti ochilgani haqida xabar.

    Yuborishdan oldin muddat qayta tekshiriladi: navbat kechiksa (masalan bot bir
    kun o'chib qolsa) allaqachon tugagan sinov haqida xabar berish yolg'on bo'lardi.
    """
    session = db.get(PersonalityTestSession, session_id)
    if session is None:
        return _cancelled("sessiya topilmadi")
    if not has_trial_premium(session):
        return _cancelled("mukofot muddati tugagan")
    left = trial_days_left(session)
    return Message(
        text=REFERRAL_REWARD_TEXT.format(days=days, left=left),
        keyboard=premium_result_keyboard(session.token),
    )


def premium_pdf_message(db: Session, session_id: int) -> Message | Outcome:
    session = db.get(PersonalityTestSession, session_id)
    if session is None:
        return _cancelled("sessiya topilmadi")
    try:
        payload = build_pdf_bytes(db, session.token, base_url=settings.public_base_url)
    except PdfNotPremium:
        return _cancelled("premium bekor qilingan")
    except PdfFontsUnavailable:
        # Deploy nuqsoni: qator terminal QILINMAYDI, shriftlar qaytarilgach yuboriladi.
        logger.error("PDF shriftlari yo‘q — hisobot keyinroqqa suriladi (sessiya %s)", session_id)
        return Outcome(error="PDF shriftlari topilmadi")
    return Message(
        document_bytes=payload,
        document_name=pdf_filename(session.result_type or "natija"),
        caption=PDF_CAPTION,
    )

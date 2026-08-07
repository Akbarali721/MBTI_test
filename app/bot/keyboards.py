"""Bot klaviaturalari — handlerlar ham, navbat ishchisi ham shu yerdan oladi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.services.premium_payment_service import signed_result_url_for_token


def result_keyboard(token: str, label: str = "Natijaga qaytish") -> InlineKeyboardMarkup | None:
    # Lokal PUBLIC_BASE_URL bilan Telegram tugmani rad etadi, shuning uchun tugmasiz yuboriladi.
    if settings.public_base_url_is_local:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, url=signed_result_url_for_token(token))]]
    )


def premium_result_keyboard(token: str | None) -> InlineKeyboardMarkup | None:
    if not token:
        return None
    return result_keyboard(token, "📊 Premium natijani ko‘rish")


def site_keyboard() -> InlineKeyboardMarkup | None:
    if settings.public_base_url_is_local:
        return None
    base = settings.public_base_url.rstrip("/")
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 Testni ochish", url=f"{base}/personality")]]
    )


def admin_receipt_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"premium_approve:{payment_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"premium_reject:{payment_id}"),
            ]
        ]
    )

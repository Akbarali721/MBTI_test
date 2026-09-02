"""Bot klaviaturalari."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    web_app_url = settings.effective_web_app_url
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Testni boshlash", web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
    )

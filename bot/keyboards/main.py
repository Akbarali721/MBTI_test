"""Bot klaviaturalari."""

from __future__ import annotations

import logging

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import settings

logger = logging.getLogger(__name__)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    info = settings.web_app_url_debug()
    web_app_url = info["final"]

    logger.info(
        "Telegram WebApp tugmasi URL | final=%s | manba=%s | "
        "WEB_APP_URL=%s | PUBLIC_BASE_URL=%s | normalize_oldin=%s",
        web_app_url,
        info["source"],
        info["WEB_APP_URL"],
        info["PUBLIC_BASE_URL"],
        info["raw_before_normalize"],
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Testni boshlash", web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
    )

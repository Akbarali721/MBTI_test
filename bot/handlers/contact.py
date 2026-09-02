"""Telefon raqamni qabul qilish."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.telegram_user_service import save_phone_number, upsert_from_bot_start, TelegramProfileInput
from bot.keyboards.main import main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()

T = TypeVar("T")


async def _run_db_commit(fn: Callable[[Session], T]) -> T:
    def _call() -> T:
        db = SessionLocal()
        try:
            result = fn(db)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return await asyncio.to_thread(_call)


@router.message(F.contact)
async def on_contact(message: Message) -> None:
    user = message.from_user
    contact = message.contact
    if user is None or contact is None:
        return

    if contact.user_id != user.id:
        await message.answer(
            "Faqat o‘zingizning telefon raqamingizni yuborishingiz mumkin.",
            reply_markup=main_menu_keyboard(),
        )
        return

    phone = (contact.phone_number or "").strip()
    if not phone:
        await message.answer("Telefon raqam topilmadi.", reply_markup=main_menu_keyboard())
        return

    profile = TelegramProfileInput(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    def _work(db: Session) -> bool:
        upsert_from_bot_start(db, profile)
        saved = save_phone_number(db, telegram_id=user.id, phone_number=phone)
        return saved is not None

    ok = await _run_db_commit(_work)
    if ok:
        await message.answer("✅ Telefon raqamingiz saqlandi.", reply_markup=main_menu_keyboard())
    else:
        await message.answer(
            "Avval /start buyrug‘ini bosing, keyin telefon raqamni yuboring.",
            reply_markup=main_menu_keyboard(),
        )

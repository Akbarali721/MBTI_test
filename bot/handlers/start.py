"""Telegram /start — foydalanuvchini saqlash va asosiy menyu."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.premium_payment_service import (
    PremiumPaymentService,
    parse_premium_session_token,
)
from app.services.telegram_user_service import TelegramProfileInput, upsert_from_bot_start
from bot.keyboards.main import main_menu_keyboard
from bot.services.referrals import attribute_bot_referral, parse_referral_telegram_id

logger = logging.getLogger(__name__)

router = Router()

START_TEXT = "Xarakteringizni 24 ta savolda aniqlang."

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


def _profile_from_message(message: Message) -> TelegramProfileInput | None:
    user = message.from_user
    if user is None:
        return None
    return TelegramProfileInput(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


async def _handle_start(message: Message, command: CommandObject | None, state: FSMContext) -> None:
    await state.clear()
    profile = _profile_from_message(message)
    if profile is None:
        return

    args = (command.args if command else None) or ""
    premium_token = parse_premium_session_token(args)
    referrer_tid = parse_referral_telegram_id(args)

    if premium_token:
        await _handle_premium_deeplink(message, profile, premium_token, state)
        return

    def _work(db: Session) -> None:
        tg_user = upsert_from_bot_start(db, profile)
        if referrer_tid is not None:
            attribute_bot_referral(db, referred=tg_user, referrer_telegram_id=referrer_tid)

    await _run_db_commit(_work)
    await message.answer(START_TEXT, reply_markup=main_menu_keyboard())


async def _handle_premium_deeplink(
    message: Message,
    profile: TelegramProfileInput,
    token: str,
    state: FSMContext,
) -> None:
    from app.bot.handlers import _PaymentView, _payment_instructions, _reply_for_session_view

    def _work(db: Session) -> _PaymentView:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=profile.telegram_id,
            telegram_username=profile.username,
            telegram_first_name=profile.first_name,
        )
        upsert_from_bot_start(db, profile)
        return _PaymentView(
            code=outcome.code,
            payment_id=outcome.payment.id if outcome.payment else None,
            session_token=outcome.session.token if outcome.session else None,
            result_type=outcome.session.result_type if outcome.session else None,
        )

    view = await _run_db_commit(_work)
    await _reply_for_session_view(
        message,
        state,
        view,
        not_found_text="Ushbu premium havola yaroqsiz yoki muddati tugagan.",
    )


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject, state: FSMContext) -> None:
    await _handle_start(message, command, state)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await _handle_start(message, None, state)

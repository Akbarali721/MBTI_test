"""Testni Telegram bot ichida o'tkazish.

Butun mantiq PersonalityService orqali ishlaydi — veb bilan bir xil savollar,
bir xil ball hisoblash va bir xil sessiya jadvali. Bot faqat interfeys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.orm import Session

from app.models.enums import AppearanceTheme
from app.personality.share_code import share_code_for_session, share_path
from app.services.personality_service import PersonalityService
from app.services.premium_payment_service import signed_result_url_for_token

logger = logging.getLogger(__name__)

router = Router()

OPTION_PREFIX = "t_opt:"
GENDER_PREFIX = "t_gender:"
OPTION_LETTERS = ("A", "B", "C", "D", "E", "F")

INTRO_TEXT = (
    "🧭 Xarakter testi\n\n"
    "24 ta savol, taxminan 4 daqiqa. To‘g‘ri yoki noto‘g‘ri javob yo‘q — "
    "odatda qanday harakat qilishingizga qarab tanlang.\n\n"
    "Boshlash uchun jinsingizni tanlang:"
)
ABANDONED_TEXT = "Avvalgi test yakunlanmagan edi. /test bilan yangisini boshlashingiz mumkin."


class TestStates(StatesGroup):
    running = State()


@dataclass(frozen=True)
class _QuestionView:
    token: str
    text: str
    question_id: int
    option_ids: tuple[int, ...]
    option_texts: tuple[str, ...]
    index: int
    total: int
    selected_option_id: int | None


@dataclass(frozen=True)
class _FinishedView:
    token: str
    result_type: str
    title: str
    short_description: str
    result_url: str
    share_url: str


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ayol", callback_data=f"{GENDER_PREFIX}female"),
                InlineKeyboardButton(text="Erkak", callback_data=f"{GENDER_PREFIX}male"),
            ]
        ]
    )


def question_keyboard(view: _QuestionView) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if option_id == view.selected_option_id else ''}{OPTION_LETTERS[position]}",
                callback_data=f"{OPTION_PREFIX}{option_id}",
            )
            for position, option_id in enumerate(view.option_ids)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_question(view: _QuestionView) -> str:
    lines = [f"Savol {view.index + 1} / {view.total}", "", view.text, ""]
    lines += [f"{OPTION_LETTERS[position]}. {text}" for position, text in enumerate(view.option_texts)]
    return "\n".join(lines)


def format_result(view: _FinishedView) -> str:
    return (
        f"✅ Test yakunlandi!\n\n"
        f"Sizning tipingiz: {view.result_type} — {view.title}\n\n"
        f"{view.short_description}\n\n"
        f"To‘liq natija va premium tahlil: {view.result_url}"
    )


def result_keyboard(view: _FinishedView) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 To‘liq natijani ochish", url=view.result_url)],
            [InlineKeyboardButton(text="🔗 Ulashish", url=view.share_url)],
        ]
    )


# --------------------------- DB ishi (sinxron) ---------------------------


def start_test(db: Session, telegram_user_id: int, gender: str) -> _QuestionView:
    service = PersonalityService(db)
    session = service.start_session(telegram_user_id=telegram_user_id, source="telegram-bot")
    service.set_appearance(session.token, AppearanceTheme(gender))
    return _question_view(service, session.token, 0)


def _question_view(service: PersonalityService, token: str, index: int | None) -> _QuestionView:
    view = service.get_test_view(token, index)
    question = view["question"]
    options = list(question.options)
    return _QuestionView(
        token=token,
        text=question.text,
        question_id=question.id,
        option_ids=tuple(option.id for option in options),
        option_texts=tuple(option.text for option in options),
        index=view["question_index"],
        total=view["total"],
        selected_option_id=view["selected_option_id"],
    )


def answer_question(
    db: Session, token: str, option_id: int
) -> tuple[_QuestionView | None, _FinishedView | None]:
    """Javobni yozadi; test tugagan bo'lsa natija ko'rinishini qaytaradi."""
    service = PersonalityService(db)
    current = service.get_test_view(token)
    if current.get("redirect") == "result":
        return None, _finished_view(db, service, token)

    question = current["question"]
    if option_id not in {option.id for option in question.options}:
        # Eski xabardagi tugma bosilgan bo'lishi mumkin — joriy savolni qayta ko'rsatamiz.
        return _question_view(service, token, current["question_index"]), None

    outcome = service.submit_answer(
        token,
        question_id=question.id,
        option_id=option_id,
        question_index=current["question_index"],
    )
    if outcome.get("redirect") in ("result", "loading"):
        return None, _finished_view(db, service, token)
    return _question_view(service, token, outcome.get("next_index")), None


def _finished_view(db: Session, service: PersonalityService, token: str) -> _FinishedView:
    view = service.get_result_view(token)
    session, content = view["session"], view["content"]
    share_code = share_code_for_session(db, session)
    from app.config import settings

    base = settings.public_base_url.rstrip("/")
    return _FinishedView(
        token=token,
        result_type=session.result_type or "",
        title=content.title,
        short_description=content.short_description,
        result_url=signed_result_url_for_token(token),
        share_url=f"{base}{share_path(share_code)}",
    )


def resume_view(db: Session, token: str) -> _QuestionView | None:
    service = PersonalityService(db)
    view = service.get_test_view(token)
    if view.get("redirect"):
        return None
    return _question_view(service, token, view["question_index"])


# --------------------------- handlerlar ---------------------------


async def _edit_or_send(message: Message, text: str, markup: InlineKeyboardMarkup | None) -> None:
    from app.bot.handlers import _safe_telegram

    edited = await _safe_telegram("edit_text", message.edit_text(text, reply_markup=markup))
    if not edited:
        await _safe_telegram("answer", message.answer(text, reply_markup=markup))


@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext) -> None:
    from app.bot.handlers import _safe_telegram

    await state.set_state(TestStates.running)
    await state.update_data(token=None)
    await _safe_telegram("answer", message.answer(INTRO_TEXT, reply_markup=gender_keyboard()))


@router.callback_query(F.data.startswith(GENDER_PREFIX))
async def cb_gender(query: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    from app.bot.handlers import _run_db, _safe_telegram

    await _safe_telegram("callback_answer", query.answer())
    user = query.from_user
    gender = (query.data or "").removeprefix(GENDER_PREFIX)
    if gender not in ("male", "female") or not isinstance(query.message, Message):
        return

    view = await _run_db(lambda db: start_test(db, user.id, gender))
    await state.set_state(TestStates.running)
    await state.update_data(token=view.token)
    await _edit_or_send(query.message, format_question(view), question_keyboard(view))


@router.callback_query(F.data.startswith(OPTION_PREFIX))
async def cb_option(query: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    from app.bot.handlers import _run_db, _safe_telegram

    await _safe_telegram("callback_answer", query.answer())
    if not isinstance(query.message, Message):
        return

    data = await state.get_data()
    token = data.get("token")
    if not token:
        await _safe_telegram("answer", query.message.answer(ABANDONED_TEXT))
        return

    try:
        option_id = int((query.data or "").removeprefix(OPTION_PREFIX))
    except ValueError:
        logger.warning("Noto‘g‘ri javob callback: %r", query.data)
        return

    question, finished = await _run_db(lambda db: answer_question(db, token, option_id))

    if finished is not None:
        await state.clear()
        await _edit_or_send(query.message, format_result(finished), result_keyboard(finished))
        return
    if question is not None:
        await _edit_or_send(query.message, format_question(question), question_keyboard(question))

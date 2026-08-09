from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ErrorEvent, Message
from sqlalchemy.orm import Session

from app.authz import ACTOR_TELEGRAM, MODERATE_PAYMENTS, AdminIdentity
from app.bot.keyboards import premium_result_keyboard, result_keyboard, site_keyboard
from app.bot.outbox_worker import run_worker
from app.config import settings
from app.database import SessionLocal
from app.models.enums import AdminRole
from app.services import audit_service
from app.services.admin_service import admin_chat_ids, telegram_identity
from app.services.notification_outbox import health as outbox_health
from app.services.premium_payment_service import (
    PremiumPaymentService,
    format_price_uzs,
    parse_premium_session_token,
    premium_bot_username,
)

logger = logging.getLogger(__name__)

router = Router()

T = TypeVar("T")

# Test kodi — tokendan olingan 8..16 belgili alfanumerik bo'lak; to'liq token ham qabul qilinadi.
_CODE_CANDIDATE_RE = re.compile(r"[A-Za-z0-9]{8,64}")
_MAX_CODE_CANDIDATES = 3

WELCOME_TEXT = (
    "Assalomu alaykum! Bu — MBTI xarakter testi boti.\n\n"
    "Testni shu yerda topshirish: /test\n\n"
    "Agar saytda topshirgan bo‘lsangiz, premium to‘lovni shu chatda rasmiylashtiring:\n"
    "1. Natija sahifasini oching va ko‘rsatilgan kartaga to‘lov qiling.\n"
    "2. Shu chatga natija sahifasidagi test kodini yuboring.\n"
    "3. So‘ng chek rasmini yoki faylini yuboring.\n\n"
    "Admin tekshirgach, premium tahlilingiz ochiladi."
)

HELP_TEXT = (
    "/test — xarakter testini shu chatda topshirish.\n\n"
    "Premium to‘lov uchun: natija sahifasidagi test kodini (kamida 8 belgi) yuboring, "
    "so‘ng chek rasmini yoki faylini tashlang."
)


class ReceiptStates(StatesGroup):
    waiting = State()


@dataclass(frozen=True)
class _PaymentView:
    """DB oqimidan tashqarida ishlatiladigan tayyor qiymatlar (ORM obyektlari emas)."""

    code: str
    payment_id: int | None = None
    session_token: str | None = None
    result_type: str | None = None
    telegram_user_id: int | None = None
    matches: int = 0
    # Chek qaysi adminlarga navbatga qo'yilgani — 0 bo'lsa moderatsiya sozlanmagan.
    admin_targets: int = 0


async def _run_db(fn: Callable[[Session], T]) -> T:
    """Sinxron DB ishini alohida oqimda bajaradi — event loop bloklanmaydi."""

    def _call() -> T:
        db = SessionLocal()
        try:
            return fn(db)
        finally:
            db.close()

    return await asyncio.to_thread(_call)


async def _run_db_commit(fn: Callable[[Session], T]) -> T:
    """`_run_db` ga o'xshash, lekin natijani COMMIT qiladi."""

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


async def _safe_telegram(action: str, coro: Awaitable[object]) -> bool:
    """Telegram chaqiruvi handlerni yiqitmasligi kerak; True — chaqiruv o‘tdi.

    DIQQAT: bu yordamchi faqat interaktiv handlerlar uchun. Navbat ishchisi undan
    foydalanmaydi — u xato TURINI bilishi kerak (bloklangan foydalanuvchi va tarmoq
    uzilishi butunlay boshqacha muomala talab qiladi).
    """
    try:
        await coro
        return True
    except TelegramForbiddenError:
        logger.warning("Telegram (%s): foydalanuvchi botni bloklagan yoki chat yopiq", action)
    except TelegramBadRequest as exc:
        logger.warning("Telegram (%s) rad etdi: %s", action, exc)
    except Exception:
        logger.exception("Telegram (%s) kutilmagan xato", action)
    return False


def _payment_instructions(result_type: str | None) -> str:
    card = settings.payment_card_number or "—"
    holder = settings.payment_card_holder or "—"
    price = format_price_uzs(settings.premium_price)
    return (
        f"Premium MBTI tahlil — {price} so‘m\n\n"
        f"Natija: {result_type or '—'}\n\n"
        f"To‘lovni quyidagi kartaga amalga oshiring:\n\n"
        f"{card}\n"
        f"{holder}\n\n"
        f"To‘lovdan keyin chek rasmini yoki faylini shu chatga yuboring.\n\n"
        f"Muhim: chek aynan shu botga yuborilishi kerak."
    )


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    token = parse_premium_session_token(command.args or "")
    if not token:
        await _safe_telegram("answer", message.answer(WELCOME_TEXT, reply_markup=site_keyboard()))
        return

    def _work(db: Session) -> _PaymentView:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=user.id,
            telegram_username=user.username,
            telegram_first_name=user.first_name,
        )
        return _PaymentView(
            code=outcome.code,
            payment_id=outcome.payment.id if outcome.payment else None,
            session_token=outcome.session.token if outcome.session else None,
            result_type=outcome.session.result_type if outcome.session else None,
        )

    view = await _run_db(_work)
    await _reply_for_session_view(
        message,
        state,
        view,
        not_found_text="Ushbu premium havola yaroqsiz yoki muddati tugagan.",
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _safe_telegram("answer", message.answer(WELCOME_TEXT, reply_markup=site_keyboard()))


@router.message(F.text)
async def on_text(message: Message, state: FSMContext) -> None:
    user = message.from_user
    text = (message.text or "").strip()
    if not user:
        return
    if text.startswith("/"):
        await _safe_telegram("answer", message.answer(HELP_TEXT, reply_markup=site_keyboard()))
        return

    candidates = _CODE_CANDIDATE_RE.findall(text)[:_MAX_CODE_CANDIDATES]
    if not candidates:
        await _safe_telegram("answer", message.answer(HELP_TEXT, reply_markup=site_keyboard()))
        return

    def _work(db: Session) -> _PaymentView:
        service = PremiumPaymentService(db)
        for candidate in candidates:
            outcome = service.claim_by_payment_code(
                payment_code=candidate,
                telegram_user_id=user.id,
                telegram_username=user.username,
                telegram_first_name=user.first_name,
            )
            if outcome.code == "not_found":
                continue
            return _PaymentView(
                code=outcome.code,
                payment_id=outcome.payment.id if outcome.payment else None,
                session_token=outcome.session.token if outcome.session else None,
                result_type=outcome.session.result_type if outcome.session else None,
                matches=outcome.matches,
            )
        return _PaymentView(code="not_found")

    view = await _run_db(_work)
    await _reply_for_session_view(
        message,
        state,
        view,
        not_found_text=(
            "Bu kod bo‘yicha test topilmadi.\n\nNatija sahifasidagi test kodini aynan nusxalab yuboring."
        ),
    )


async def _reply_for_session_view(
    message: Message,
    state: FSMContext,
    view: _PaymentView,
    *,
    not_found_text: str,
) -> None:
    if view.code in ("not_found", "invalid_token"):
        await _safe_telegram("answer", message.answer(not_found_text, reply_markup=site_keyboard()))
        return
    if view.code == "ambiguous":
        await _safe_telegram(
            "answer",
            message.answer(
                f"Bu kod bo‘yicha {view.matches} ta test topildi. "
                "Iltimos, natija sahifasidagi havolani to‘liq yuboring."
            ),
        )
        return
    if view.code == "incomplete":
        await _safe_telegram(
            "answer",
            message.answer("Avval testni oxirigacha tugating.", reply_markup=site_keyboard()),
        )
        return
    if view.code == "already_premium":
        await _safe_telegram(
            "answer",
            message.answer(
                "Premium tahlilingiz allaqachon ochilgan.",
                reply_markup=premium_result_keyboard(view.session_token),
            ),
        )
        return
    if view.code == "owned_by_other":
        await _safe_telegram(
            "answer",
            message.answer(
                "Bu test boshqa Telegram akkauntga biriktirilgan va uning faol to‘lovi bor.\n\n"
                "Agar bu sizning testingiz bo‘lsa, o‘sha akkauntdan davom eting yoki admin bilan bog‘laning."
            ),
        )
        return
    if view.payment_id is None or view.session_token is None:
        await _safe_telegram(
            "answer",
            message.answer("So‘rovni ochib bo‘lmadi. Iltimos, birozdan so‘ng qayta urinib ko‘ring."),
        )
        return

    await state.set_state(ReceiptStates.waiting)
    await state.update_data(payment_id=view.payment_id, session_token=view.session_token)
    await _safe_telegram(
        "answer",
        message.answer(
            _payment_instructions(view.result_type),
            reply_markup=result_keyboard(view.session_token),
        ),
    )


@router.message(F.photo)
async def on_receipt_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    await _handle_receipt(message, state, bot, receipt_type="photo")


@router.message(F.document)
async def on_receipt_document(message: Message, state: FSMContext, bot: Bot) -> None:
    await _handle_receipt(message, state, bot, receipt_type="document")


@router.message()
async def on_unknown(message: Message) -> None:
    await _safe_telegram("answer", message.answer(HELP_TEXT, reply_markup=site_keyboard()))


async def _handle_receipt(message: Message, state: FSMContext, bot: Bot, *, receipt_type: str) -> None:
    user = message.from_user
    if not user:
        return

    file_id: str | None = None
    if receipt_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif receipt_type == "document" and message.document:
        file_id = message.document.file_id
    if not file_id:
        return

    # FSM'dagi payment_id ustuvor: foydalanuvchida bir nechta faol so'rov bo'lsa ham
    # chek aynan shu suhbatda ochilgan so'rovga tushadi.
    data = await state.get_data()
    payment_id = _as_payment_id(data.get("payment_id"))

    def _work(db: Session) -> _PaymentView:
        outcome = PremiumPaymentService(db).attach_receipt(
            telegram_user_id=user.id,
            receipt_file_id=file_id,
            receipt_type=receipt_type,
            payment_id=payment_id,
        )
        payment = outcome.payment
        return _PaymentView(
            code=outcome.code,
            payment_id=payment.id if payment else None,
            session_token=payment.session.token if payment and payment.session else None,
            admin_targets=len(admin_chat_ids(db)),
        )

    view = await _run_db(_work)

    if view.code == "no_active_payment":
        await _safe_telegram(
            "answer",
            message.answer(
                "Faol premium so‘rov topilmadi.\n\nAvval natija sahifasidagi test kodini shu chatga yuboring."
            ),
        )
        return
    if view.code == "already_approved":
        await state.clear()
        await _safe_telegram(
            "answer",
            message.answer(
                "Premium allaqachon ochilgan.",
                reply_markup=premium_result_keyboard(view.session_token),
            ),
        )
        return
    if view.code != "saved" or view.payment_id is None:
        logger.error("Chekni saqlab bo‘lmadi: user=%s code=%s", user.id, view.code)
        await _safe_telegram(
            "answer",
            message.answer("Chekni qabul qilib bo‘lmadi. Iltimos, qayta urinib ko‘ring."),
        )
        return

    await state.clear()
    await _safe_telegram(
        "answer",
        message.answer("✅ Chek qabul qilindi.\n\nAdmin tekshirgach, premium tahlilingiz ochiladi."),
    )

    # Adminga xabar `attach_receipt` ichida, chek bilan BIR tranzaksiyada navbatga
    # qo'yildi. Bu yerda faqat manzil borligini tekshiramiz: hech qanday admin
    # sozlanmagan bo'lsa, xabar hech qachon yetib bormaydi va mijoz buni bilishi kerak.
    if not view.admin_targets:
        logger.error("Hech qanday admin sozlanmagan: #%s cheki moderatsiyaga bormaydi", view.payment_id)
        await _safe_telegram(
            "answer",
            message.answer(
                "Eslatma: chek saqlandi, lekin adminga avtomatik xabar bormadi. "
                "Javob kechiksa, admin bilan bog‘laning."
            ),
        )


def _as_payment_id(raw: object) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return None
    return None


@router.callback_query(F.data.startswith("premium_approve:"))
async def cb_approve(query: CallbackQuery, bot: Bot) -> None:
    await _moderate(query, bot, approve=True)


@router.callback_query(F.data.startswith("premium_reject:"))
async def cb_reject(query: CallbackQuery, bot: Bot) -> None:
    await _moderate(query, bot, approve=False)


async def _moderate(query: CallbackQuery, bot: Bot, *, approve: bool) -> None:
    user = query.from_user
    if user is None:
        return

    # Rol tekshiruvi: `admin_users` da qatori bor "kuzatuvchi" ham botda tugma
    # bosib to'lov tasdiqlay olmasligi kerak.
    identity = await _resolve_admin(user.id)
    if identity is None or not identity.can(MODERATE_PAYMENTS):
        await _safe_telegram("callback_answer", query.answer("Ruxsat yo‘q", show_alert=True))
        return

    payment_id = _payment_id_from_callback(query.data)
    if payment_id is None:
        logger.warning("Noto‘g‘ri callback data: %r", query.data)
        await _safe_telegram("callback_answer", query.answer("Noto‘g‘ri so‘rov", show_alert=True))
        return

    actor = identity.audit_actor

    def _work(db: Session) -> _PaymentView:
        service = PremiumPaymentService(db)
        outcome = (
            service.approve_payment(payment_id, approved_by=actor)
            if approve
            else service.reject_payment(payment_id, approved_by=actor)
        )
        if outcome.code in ("approved", "rejected"):
            audit_service.record(
                db,
                identity,
                audit_service.PAYMENT_APPROVED if approve else audit_service.PAYMENT_REJECTED,
                target_type="payment",
                target_id=payment_id,
            )
        return _PaymentView(
            code=outcome.code,
            payment_id=outcome.payment.id if outcome.payment else None,
            session_token=outcome.session.token if outcome.session else None,
            telegram_user_id=outcome.payment.telegram_user_id if outcome.payment else None,
        )

    view = await _run_db_commit(_work)

    # Avval tugmani javobsiz qoldirmaymiz va klaviaturani tozalaymiz: mijozga xabar
    # yuborish muvaffaqiyatsiz bo'lsa ham admin panelida "aylanish" qolmaydi.
    done = view.code == _done_code(approve)
    answer_text = _MODERATION_ANSWERS.get(view.code, "Bajarildi")
    await _safe_telegram("callback_answer", query.answer(answer_text, show_alert=not done))
    if isinstance(query.message, Message):
        await _safe_telegram("edit_markup", query.message.edit_reply_markup(reply_markup=None))
    if not done:
        return

    # Mijozga xabar va PDF `approve_payment`/`reject_payment` ichida navbatga
    # qo'yildi — bu yerdan to'g'ridan-to'g'ri yuborish takroriy xabar bo'lardi.
    if not view.telegram_user_id:
        logger.warning("#%s to‘lovda Telegram ID yo‘q — foydalanuvchiga xabar yuborilmadi", payment_id)
        if isinstance(query.message, Message):
            await _safe_telegram(
                "answer",
                query.message.answer(
                    f"#{payment_id}: foydalanuvchining Telegram ID si yo‘q, unga xabar yuborilmadi."
                ),
            )


_MODERATION_ANSWERS = {
    "approved": "Tasdiqlandi",
    "rejected": "Rad etildi",
    "already_approved": "Allaqachon tasdiqlangan",
    "already_premium": "Sessiya allaqachon premium",
    "not_found": "So‘rov topilmadi",
}


def _done_code(approve: bool) -> str:
    return "approved" if approve else "rejected"


def _payment_id_from_callback(data: str | None) -> int | None:
    if not data or ":" not in data:
        return None
    try:
        return int(data.split(":", 1)[1])
    except ValueError:
        return None


async def _resolve_admin(telegram_user_id: int) -> AdminIdentity | None:
    """Telegram foydalanuvchisi uchun admin shaxsi.

    `.env` ro'yxati avval va HECH QANDAY I/O siz tekshiriladi: baza javob bermay
    qolsa ham asosiy egasi moderatsiya qila olishi kerak. Bazaga murojaat esa
    `_run_db` orqali, ya'ni event loop bloklanmaydi.
    """
    if telegram_user_id in settings.admin_telegram_id_set:
        return AdminIdentity(
            username=str(telegram_user_id),
            role=AdminRole.OWNER,
            telegram_user_id=telegram_user_id,
            actor_type=ACTOR_TELEGRAM,
        )
    try:
        return await _run_db(lambda db: telegram_identity(db, telegram_user_id))
    except Exception:
        # Fail-closed: baza yo'q bo'lsa faqat `.env` dagi adminlar ishlaydi.
        logger.exception("Admin ro‘yxatini o‘qib bo‘lmadi")
        return None


ERROR_TEXT = "Xatolik yuz berdi. Birozdan so‘ng qayta urinib ko‘ring."


async def on_unhandled_error(event: ErrorEvent) -> bool:
    logger.exception("Bot handlerida kutilmagan xato", exc_info=event.exception)
    update = event.update
    if update.callback_query is not None:
        await _safe_telegram(
            "callback_answer",
            update.callback_query.answer(ERROR_TEXT, show_alert=True),
        )
    elif isinstance(update.message, Message):
        await _safe_telegram("answer", update.message.answer(ERROR_TEXT))
    return True


def create_dispatcher() -> Dispatcher:
    from app.bot import test_flow

    dp = Dispatcher()
    # Test oqimi avval ro'yxatdan o'tadi: uning callback'lari va /test buyrug'i
    # umumiy matn/fallback handlerlariga tushib ketmasligi kerak.
    dp.include_router(test_flow.router)
    dp.include_router(router)
    dp.errors.register(on_unhandled_error)
    return dp


async def check_bot_configuration(bot: Bot) -> list[str]:
    """Ishga tushishdagi self-check: noto‘g‘ri sozlama jim qolmasligi kerak."""
    problems: list[str] = []

    configured = premium_bot_username()
    try:
        me = await bot.get_me()
    except Exception as exc:
        problems.append(f"getMe muvaffaqiyatsiz — BOT_TOKEN noto‘g‘ri bo‘lishi mumkin: {exc}")
    else:
        actual = (me.username or "").lstrip("@")
        if not configured:
            problems.append(
                f"BOT_USERNAME sozlanmagan; natija sahifasidagi havolalar ishlamaydi (haqiqiy bot: @{actual})"
            )
        elif configured.lower() != actual.lower():
            problems.append(
                f"BOT_USERNAME/@PAYMENT_SUPPORT_BOT_USERNAME '@{configured}', "
                f"lekin token '@{actual}' botiga tegishli — foydalanuvchi boshqa botga yuborilmoqda"
            )

    try:
        targets = await _run_db(admin_chat_ids)
    except Exception:
        logger.exception("Admin ro‘yxatini o‘qib bo‘lmadi")
        targets = sorted(settings.admin_telegram_id_set)
    if not targets:
        problems.append(
            "Hech qanday admin sozlanmagan (ADMIN_TELEGRAM_IDS yoki admin_users) — "
            "cheklar moderatsiyaga bormaydi"
        )

    try:
        overdue = await _run_db(lambda db: outbox_health(db).overdue_pending)
    except Exception:
        logger.exception("Bildirishnoma navbatini o‘qib bo‘lmadi")
        overdue = 0
    if overdue:
        problems.append(f"Navbatda {overdue} ta kechikkan bildirishnoma bor")

    if settings.public_base_url_is_local:
        problems.append(
            f"PUBLIC_BASE_URL lokal manzil ({settings.public_base_url}) — natija tugmalari ishlamaydi"
        )

    return problems


async def run_bot() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    bot = Bot(token=settings.bot_token)
    worker: asyncio.Task[None] | None = None
    try:
        for problem in await check_bot_configuration(bot):
            logger.warning("Bot sozlamasi ogohlantirishi: %s", problem)
        dp = create_dispatcher()
        # Navbat ishchisi AYNAN shu jarayonda: bot konteyneri yagona nusxada
        # ishlaydi, uvicorn esa bir nechta ishchi bilan ishga tushishi mumkin —
        # u yerda navbat bir necha marta yuborilardi.
        worker = asyncio.create_task(run_worker(bot))
        await dp.start_polling(bot)
    finally:
        if worker is not None:
            # Sessiya yopilishidan OLDIN to'xtatiladi, aks holda yuborish o'rtasida
            # "Session is closed" xatosi chiqib, qator noto'g'ri belgilanardi.
            worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker
        await bot.session.close()

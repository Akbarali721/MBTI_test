from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import settings
from app.database import SessionLocal
from app.services.premium_payment_service import PremiumPaymentService, parse_premium_session_token, result_url_for_token

router = Router()


class ReceiptStates(StatesGroup):
    waiting = State()


def _format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def _result_keyboard(token: str, label: str = "Natijaga qaytish") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, url=result_url_for_token(token))]]
    )


def _admin_receipt_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"premium_approve:{payment_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"premium_reject:{payment_id}"),
            ]
        ]
    )


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandStart, state: FSMContext) -> None:
    args = command.args or ""
    if not args.startswith("premium_"):
        await message.answer("Assalomu alaykum! Premium uchun natija sahifasidagi havoladan foydalaning.")
        return

    token = parse_premium_session_token(args)
    if not token:
        await message.answer("Ushbu premium havola yaroqsiz yoki muddati tugagan.")
        return

    user = message.from_user
    if not user:
        return

    db = SessionLocal()
    try:
        service = PremiumPaymentService(db)
        outcome = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=user.id,
            telegram_username=user.username,
            telegram_first_name=user.first_name,
        )
        session = outcome.session
        payment = outcome.payment

        if outcome.code == "invalid_token":
            await message.answer("Ushbu premium havola yaroqsiz yoki muddati tugagan.")
            return
        if not session:
            await message.answer("Ushbu premium havola yaroqsiz yoki muddati tugagan.")
            return
        if outcome.code == "incomplete":
            await message.answer("Avval testni oxirigacha tugating.")
            return
        if outcome.code == "already_premium":
            await message.answer(
                "Premium tahlilingiz allaqachon ochilgan.",
                reply_markup=_result_keyboard(session.token, "📊 Premium natijani ko‘rish"),
            )
            return

        assert payment is not None
        await state.set_state(ReceiptStates.waiting)
        await state.update_data(payment_id=payment.id, session_token=session.token)

        card = settings.payment_card_number or "—"
        holder = settings.payment_card_holder or "—"
        price = _format_price(settings.premium_price)
        text = (
            f"Premium MBTI tahlil — {price} so‘m\n\n"
            f"Natija: {session.result_type or '—'}\n\n"
            f"To‘lovni quyidagi kartaga amalga oshiring:\n\n"
            f"{card}\n"
            f"{holder}\n\n"
            f"To‘lovdan keyin chek rasmini yoki faylini shu chatga yuboring.\n\n"
            f"Muhim: chek aynan shu botga yuborilishi kerak."
        )
        await message.answer(text, reply_markup=_result_keyboard(session.token))
    finally:
        db.close()


@router.message(F.photo)
async def on_receipt_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    await _handle_receipt(message, state, bot, receipt_type="photo")


@router.message(F.document)
async def on_receipt_document(message: Message, state: FSMContext, bot: Bot) -> None:
    await _handle_receipt(message, state, bot, receipt_type="document")


async def _handle_receipt(message: Message, state: FSMContext, bot: Bot, *, receipt_type: str) -> None:
    user = message.from_user
    if not user:
        return

    data = await state.get_data()
    payment_id = data.get("payment_id")

    file_id: str | None = None
    if receipt_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif receipt_type == "document" and message.document:
        file_id = message.document.file_id
    if not file_id:
        return

    db = SessionLocal()
    try:
        service = PremiumPaymentService(db)
        outcome = service.attach_receipt(
            telegram_user_id=user.id,
            receipt_file_id=file_id,
            receipt_type=receipt_type,
            payment_id=int(payment_id) if payment_id else None,
        )
        if outcome.code == "no_active_payment":
            await message.answer("Faol premium so‘rov topilmadi. Natija sahifasidagi havola orqali qayta boshlang.")
            return
        if outcome.code == "already_approved":
            await message.answer("Premium allaqachon ochilgan.")
            return
        if outcome.code != "saved" or not outcome.payment:
            await message.answer("Chekni qabul qilib bo‘lmadi. Iltimos, qayta urinib ko‘ring.")
            return

        payment = outcome.payment
        await message.answer(
            "✅ Chek qabul qilindi.\n\nAdmin tekshirgach, premium tahlilingiz ochiladi."
        )
        await _notify_admin_receipt(bot, message, payment.id)
    finally:
        db.close()


async def _notify_admin_receipt(bot: Bot, message: Message, payment_id: int) -> None:
    admin_id = settings.admin_telegram_id
    if not admin_id:
        return

    db = SessionLocal()
    try:
        from app.repositories.payment_repository import PaymentRepository

        payment = PaymentRepository(db).get_by_id_with_session(payment_id)
        if not payment or not payment.session:
            return
        session = payment.session
        username = f"@{payment.telegram_username}" if payment.telegram_username else "—"
        caption = (
            "Yangi premium chek\n\n"
            f"Payment ID: {payment.id}\n"
            f"User: {payment.telegram_first_name or '—'}\n"
            f"Username: {username}\n"
            f"Telegram ID: {payment.telegram_user_id}\n"
            f"Session ID: {session.id}\n"
            f"MBTI: {session.result_type or '—'}\n"
            f"Amount: {_format_price(payment.amount)} so‘m"
        )
        keyboard = _admin_receipt_keyboard(payment.id)
        if message.photo:
            await bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
        elif message.document:
            await bot.send_document(admin_id, message.document.file_id, caption=caption, reply_markup=keyboard)
    finally:
        db.close()


@router.callback_query(F.data.startswith("premium_approve:"))
async def cb_approve(query: CallbackQuery, bot: Bot) -> None:
    if not _is_admin(query):
        await query.answer("Ruxsat yo‘q", show_alert=True)
        return
    payment_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        service = PremiumPaymentService(db)
        outcome = service.approve_payment(payment_id, approved_by=f"telegram:{query.from_user.id}")
        if outcome.code in ("not_found",):
            await query.answer("So‘rov topilmadi", show_alert=True)
            return
        if outcome.session and outcome.payment:
            await bot.send_message(
                outcome.payment.telegram_user_id,
                "✅ To‘lov tasdiqlandi!\n\nPremium MBTI tahlilingiz ochildi.",
                reply_markup=_result_keyboard(outcome.session.token, "📊 Premium natijani ko‘rish"),
            )
        await query.answer("Tasdiqlandi")
        if query.message:
            await query.message.edit_reply_markup(reply_markup=None)
    finally:
        db.close()


@router.callback_query(F.data.startswith("premium_reject:"))
async def cb_reject(query: CallbackQuery, bot: Bot) -> None:
    if not _is_admin(query):
        await query.answer("Ruxsat yo‘q", show_alert=True)
        return
    payment_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        service = PremiumPaymentService(db)
        outcome = service.reject_payment(payment_id, approved_by=f"telegram:{query.from_user.id}")
        if outcome.code == "already_approved":
            await query.answer("Allaqachon tasdiqlangan", show_alert=True)
            return
        if outcome.payment:
            await bot.send_message(
                outcome.payment.telegram_user_id,
                "❌ To‘lovni tasdiqlab bo‘lmadi.\n\n"
                "Iltimos, to‘g‘ri chekni qayta yuboring yoki admin bilan bog‘laning.",
            )
        await query.answer("Rad etildi")
        if query.message:
            await query.message.edit_reply_markup(reply_markup=None)
    finally:
        db.close()


def _is_admin(query: CallbackQuery) -> bool:
    if settings.admin_telegram_id is None:
        return False
    return query.from_user is not None and query.from_user.id == settings.admin_telegram_id


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher()
    await dp.start_polling(bot)

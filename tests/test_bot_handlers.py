"""Bot qatlami — pul yoʻli: deep-link, test kodi, chek va moderatsiya.

aiogram obyektlari haqiqiy modellardan meros oladi (handlerlar `isinstance` tekshiradi),
tarmoqqa chiqadigan metodlar esa chaqiruvlarni yozib boradigan soxta metodlar bilan
almashtirilgan. Bot obyekti — `AsyncMock`. FSM haqiqiy `MemoryStorage` ustida ishlaydi.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    Chat,
    Document,
    ErrorEvent,
    Message,
    PhotoSize,
    Update,
    User,
)
from pydantic import Field
from sqlalchemy import func, select

from app.bot import handlers
from app.config import settings
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityTestSession
from app.services import premium_payment_service
from app.services.premium_payment_service import PremiumPaymentService
from tests.helpers import (
    complete_session,
    db_session,
    latest_session,
    payment_code_for_token,
    session_by_token,
)

ADMIN_ID = 424242


# --------------------------------------------------------------------------- soxta obyektlar


class CallLog(list):
    """Barcha tashqi chaqiruvlar bitta roʻyxatda — tartibni ham tekshirish mumkin."""

    def names(self) -> list[str]:
        return [name for name, _ in self]

    def texts(self, name: str) -> list[str]:
        return [text for entry, text in self if entry == name]

    def last_text(self, name: str) -> str:
        texts = self.texts(name)
        assert texts, f"{name} umuman chaqirilmagan; chaqirilganlari: {self.names()}"
        return texts[-1]


class FakeMessage(Message):
    # `log` — Any: pydantic uni qayta qurmaydi, shuning uchun roʻyxat testdagisi bilan bir xil.
    log: Any = Field(default=None)

    async def answer(self, text: str, **_kwargs: Any) -> FakeMessage:
        self.log.append(("answer", text))
        return self

    async def edit_reply_markup(self, **_kwargs: Any) -> bool:
        self.log.append(("edit_reply_markup", ""))
        return True


class FakeCallbackQuery(CallbackQuery):
    log: Any = Field(default=None)

    async def answer(self, text: str | None = None, show_alert: bool | None = None, **_k: Any) -> bool:
        self.log.append(("callback_answer", text or ""))
        return True


def make_message(
    log: CallLog,
    *,
    user_id: int = 1001,
    text: str | None = None,
    photo: bool = False,
    document: bool = False,
    username: str | None = "payer",
    first_name: str = "Ali",
) -> FakeMessage:
    return FakeMessage(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name=first_name, username=username),
        text=text,
        photo=(
            [PhotoSize(file_id="photo-file", file_unique_id="pu", width=90, height=90)] if photo else None
        ),
        document=(Document(file_id="doc-file", file_unique_id="du") if document else None),
        log=log,
    )


def make_callback(log: CallLog, data: str, *, user_id: int, with_message: bool = True) -> FakeCallbackQuery:
    return FakeCallbackQuery(
        id="cb-1",
        from_user=User(id=user_id, is_bot=False, first_name="Admin"),
        chat_instance="chat-instance",
        data=data,
        message=make_message(log, user_id=user_id) if with_message else None,
        log=log,
    )


def make_state(user_id: int = 1001) -> FSMContext:
    return FSMContext(storage=MemoryStorage(), key=StorageKey(bot_id=1, chat_id=user_id, user_id=user_id))


def make_bot(log: CallLog) -> AsyncMock:
    bot = AsyncMock()
    for name in ("send_message", "send_photo", "send_document"):
        getattr(bot, name).side_effect = _record(log, name)
    return bot


def _record(log: CallLog, name: str):
    async def _call(*args: Any, **kwargs: Any) -> bool:
        payload = kwargs.get("caption") or kwargs.get("text") or (args[1] if len(args) > 1 else "")
        log.append((name, str(payload)))
        return True

    return _call


def run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- fixtures


@pytest.fixture()
def bot_db(client, monkeypatch):
    """Handlerlar DB sessiyasini `SessionLocal` orqali ochadi — uni test bazasiga qaratamiz."""
    monkeypatch.setattr(handlers, "SessionLocal", client.testing_session_factory)
    return client


@pytest.fixture()
def admin_id(monkeypatch) -> int:
    monkeypatch.setattr(settings, "admin_telegram_id", ADMIN_ID)
    return ADMIN_ID


def start_command(payload: str) -> CommandObject:
    return CommandObject(prefix="/", command="start", args=payload)


def open_payment(client, token: str, telegram_user_id: int) -> int:
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=telegram_user_id,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
        assert outcome.payment is not None
        return outcome.payment.id


# --------------------------------------------------------------------------- /start deep-link


def test_deeplink_with_unknown_token_tells_user(bot_db):
    log = CallLog()
    run(handlers.cmd_start_deeplink(make_message(log), start_command("premium_yoqbundaytoken"), make_state()))
    assert "yaroqsiz" in log.last_text("answer")


def test_deeplink_without_premium_payload_shows_welcome(bot_db):
    log = CallLog()
    run(handlers.cmd_start_deeplink(make_message(log), start_command("boshqa-payload"), make_state()))
    assert log.last_text("answer") == handlers.WELCOME_TEXT


def test_deeplink_on_incomplete_test_asks_to_finish(bot_db, client):
    client.get("/personality/instructions")
    with db_session(client) as db:
        token = latest_session(db).token

    log = CallLog()
    run(handlers.cmd_start_deeplink(make_message(log), start_command(f"premium_{token}"), make_state()))
    assert "Avval testni oxirigacha tugating" in log.last_text("answer")


def test_deeplink_creates_payment_and_arms_receipt_state(bot_db, client):
    token = complete_session(client)
    log, state = CallLog(), make_state(555)

    run(handlers.cmd_start_deeplink(make_message(log, user_id=555), start_command(f"premium_{token}"), state))

    assert "Premium MBTI tahlil" in log.last_text("answer")
    assert run(state.get_state()) == handlers.ReceiptStates.waiting.state
    data = run(state.get_data())
    assert data["session_token"] == token
    with db_session(client) as db:
        payment = db.scalar(select(PaymentRequest))
        assert payment is not None
        assert payment.id == data["payment_id"]
        assert payment.telegram_user_id == 555
        assert session_by_token(db, token).telegram_user_id == 555


def test_deeplink_on_already_premium_session(bot_db, client):
    token = complete_session(client)
    with db_session(client) as db:
        session_by_token(db, token).is_premium = True
        db.commit()

    log = CallLog()
    run(handlers.cmd_start_deeplink(make_message(log), start_command(f"premium_{token}"), make_state()))
    assert "allaqachon ochilgan" in log.last_text("answer")


def test_deeplink_refuses_session_owned_by_another_account(bot_db, client):
    token = complete_session(client)
    owner_log = CallLog()
    run(
        handlers.cmd_start_deeplink(
            make_message(owner_log, user_id=111), start_command(f"premium_{token}"), make_state(111)
        )
    )

    stranger_log = CallLog()
    run(
        handlers.cmd_start_deeplink(
            make_message(stranger_log, user_id=222), start_command(f"premium_{token}"), make_state(222)
        )
    )

    assert "boshqa Telegram akkauntga biriktirilgan" in stranger_log.last_text("answer")
    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1
        assert session_by_token(db, token).telegram_user_id == 111


def test_plain_start_answers_and_clears_state(bot_db):
    log, state = CallLog(), make_state()
    run(state.set_state(handlers.ReceiptStates.waiting))
    run(state.update_data(payment_id=7))

    run(handlers.cmd_start(make_message(log, text="/start"), state))

    assert log.last_text("answer") == handlers.WELCOME_TEXT
    assert run(state.get_state()) is None
    assert run(state.get_data()) == {}


# --------------------------------------------------------------------------- matn (test kodi)


def test_test_code_claims_web_payment_left_without_telegram_id(bot_db, client):
    """Vebda boshlangan toʻlovda telegram_user_id NULL — aynan shu qator qutqariladi."""
    token = complete_session(client)
    assert client.post(f"/personality/result/{token}/support-bot", follow_redirects=False).status_code == 303
    code = payment_code_for_token(client, token)
    with db_session(client) as db:
        assert db.scalar(select(PaymentRequest)).telegram_user_id is None

    log, state = CallLog(), make_state(987654)
    run(handlers.on_text(make_message(log, user_id=987654, text=code), state))

    assert "Premium MBTI tahlil" in log.last_text("answer")
    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1
        payment = db.scalar(select(PaymentRequest))
        assert payment.telegram_user_id == 987654
        assert session_by_token(db, token).telegram_user_id == 987654
    assert run(state.get_data())["payment_id"] == payment.id


def test_test_code_inside_a_sentence_is_still_found(bot_db, client):
    token = complete_session(client)
    code = payment_code_for_token(client, token)

    log = CallLog()
    run(
        handlers.on_text(
            make_message(log, user_id=4321, text=f"Salom, mening kodim: {code}"), make_state(4321)
        )
    )

    assert "Premium MBTI tahlil" in log.last_text("answer")
    with db_session(client) as db:
        assert session_by_token(db, token).telegram_user_id == 4321


def test_unknown_test_code_gets_a_clear_error(bot_db):
    log = CallLog()
    run(handlers.on_text(make_message(log, text="abcdefgh12345678"), make_state()))
    assert "Bu kod bo‘yicha test topilmadi" in log.last_text("answer")


def test_ambiguous_test_code_asks_for_the_full_link(bot_db, monkeypatch):
    # payment_code ustuni unique, shuning uchun haqiqiy dublikat yaratib boʻlmaydi;
    # bu yerda faqat topilganlar soni muhim (eski, kodsiz qatorlardan qolgan holat).
    monkeypatch.setattr(
        premium_payment_service,
        "find_sessions_by_payment_code",
        lambda _db, _code, **_kwargs: [object(), object()],
    )
    log = CallLog()
    run(handlers.on_text(make_message(log, text="takrorlanuvchi"), make_state()))
    assert "2 ta test topildi" in log.last_text("answer")


def test_unknown_command_gets_help(bot_db):
    log = CallLog()
    run(handlers.on_text(make_message(log, text="/nomalum"), make_state()))
    assert log.last_text("answer") == handlers.HELP_TEXT


def test_text_without_a_code_candidate_gets_help(bot_db):
    log = CallLog()
    run(handlers.on_text(make_message(log, text="salom"), make_state()))
    assert log.last_text("answer") == handlers.HELP_TEXT


def test_fallback_handler_is_never_silent(bot_db):
    log = CallLog()
    run(handlers.on_unknown(make_message(log)))
    assert log.last_text("answer") == handlers.HELP_TEXT


# --------------------------------------------------------------------------- chek


def test_photo_receipt_is_saved_and_forwarded_to_admin(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 1001)
    log, state = CallLog(), make_state(1001)
    run(state.update_data(payment_id=payment_id, session_token=token))

    run(handlers.on_receipt_photo(make_message(log, user_id=1001, photo=True), state, make_bot(log)))

    with db_session(client) as db:
        payment = db.get(PaymentRequest, payment_id)
        assert payment.status == "receipt_sent"
        assert payment.receipt_type == "photo"
        assert payment.receipt_file_id == "photo-file"
    assert "Chek qabul qilindi" in log.texts("answer")[0]
    assert f"Payment ID: {payment_id}" in log.last_text("send_photo")
    assert run(state.get_data()) == {}


def test_document_receipt_uses_send_document(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 1002)
    log, state = CallLog(), make_state(1002)
    run(state.update_data(payment_id=payment_id))

    run(handlers.on_receipt_document(make_message(log, user_id=1002, document=True), state, make_bot(log)))

    assert "send_document" in log.names()
    with db_session(client) as db:
        payment = db.get(PaymentRequest, payment_id)
        assert payment.receipt_type == "document"
        assert payment.receipt_file_id == "doc-file"


def test_receipt_without_an_open_request_explains_next_step(bot_db, admin_id):
    log = CallLog()
    run(
        handlers.on_receipt_photo(
            make_message(log, user_id=5555, photo=True), make_state(5555), make_bot(log)
        )
    )
    assert "Faol premium so‘rov topilmadi" in log.last_text("answer")


def test_receipt_after_approval_points_back_to_the_result(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 1003)
    with db_session(client) as db:
        PremiumPaymentService(db).approve_payment(payment_id, approved_by="test")

    log, state = CallLog(), make_state(1003)
    run(state.update_data(payment_id=payment_id))
    run(handlers.on_receipt_photo(make_message(log, user_id=1003, photo=True), state, make_bot(log)))

    assert "Premium allaqachon ochilgan" in log.last_text("answer")
    assert "send_photo" not in log.names()


def test_receipt_after_rejection_creates_a_new_audit_row(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 1004)
    with db_session(client) as db:
        PremiumPaymentService(db).reject_payment(payment_id, approved_by="admin")

    log = CallLog()
    run(
        handlers.on_receipt_photo(
            make_message(log, user_id=1004, photo=True), make_state(1004), make_bot(log)
        )
    )

    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        rows = list(
            db.scalars(select(PaymentRequest).where(PaymentRequest.session_id == session_id).order_by("id"))
        )
    assert len(rows) == 2, "rad etilgan urinish tarixda qolishi kerak"
    assert rows[0].id == payment_id
    assert rows[0].status == "rejected"
    assert rows[1].status == "receipt_sent"
    assert rows[1].receipt_file_id == "photo-file"


def test_receipt_warns_user_when_admin_is_not_configured(bot_db, client, monkeypatch):
    monkeypatch.setattr(settings, "admin_telegram_id", None)
    token = complete_session(client)
    payment_id = open_payment(client, token, 1005)
    log, state = CallLog(), make_state(1005)
    run(state.update_data(payment_id=payment_id))

    run(handlers.on_receipt_photo(make_message(log, user_id=1005, photo=True), state, make_bot(log)))

    assert "adminga avtomatik xabar bormadi" in log.last_text("answer")


# --------------------------------------------------------------------------- moderatsiya


def test_is_admin_is_fail_closed_without_admin_telegram_id(bot_db, monkeypatch):
    monkeypatch.setattr(settings, "admin_telegram_id", None)
    log = CallLog()
    query = make_callback(log, "premium_approve:1", user_id=ADMIN_ID)

    assert handlers._is_admin(query) is False

    run(handlers.cb_approve(query, make_bot(log)))
    assert log.last_text("callback_answer") == "Ruxsat yo‘q"
    assert "send_message" not in log.names()


def test_stranger_cannot_moderate_a_payment(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 2001)
    log = CallLog()

    run(
        handlers.cb_approve(
            make_callback(log, f"premium_approve:{payment_id}", user_id=admin_id + 1), make_bot(log)
        )
    )

    assert log.last_text("callback_answer") == "Ruxsat yo‘q"
    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is False


def test_approve_answers_the_callback_before_messaging_the_user(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 2002)
    log = CallLog()

    run(
        handlers.cb_approve(
            make_callback(log, f"premium_approve:{payment_id}", user_id=admin_id), make_bot(log)
        )
    )

    names = log.names()
    assert "callback_answer" in names and "send_message" in names
    assert names.index("callback_answer") < names.index("send_message"), names
    assert log.last_text("callback_answer") == "Tasdiqlandi"
    assert "To‘lov tasdiqlandi" in log.last_text("send_message")
    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is True


def test_reject_answers_the_callback_first_and_keeps_premium_closed(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 2003)
    log = CallLog()

    run(
        handlers.cb_reject(
            make_callback(log, f"premium_reject:{payment_id}", user_id=admin_id), make_bot(log)
        )
    )

    names = log.names()
    assert names.index("callback_answer") < names.index("send_message"), names
    assert log.last_text("callback_answer") == "Rad etildi"
    assert "To‘lovni tasdiqlab bo‘lmadi" in log.last_text("send_message")
    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is False


def test_moderation_clears_the_inline_keyboard(bot_db, client, admin_id):
    token = complete_session(client)
    payment_id = open_payment(client, token, 2004)
    log = CallLog()

    run(
        handlers.cb_approve(
            make_callback(log, f"premium_approve:{payment_id}", user_id=admin_id), make_bot(log)
        )
    )

    assert "edit_reply_markup" in log.names()


def test_broken_callback_data_still_answers_the_button(bot_db, admin_id):
    log = CallLog()
    run(handlers.cb_approve(make_callback(log, "premium_approve:xyz", user_id=admin_id), make_bot(log)))
    assert log.last_text("callback_answer") == "Noto‘g‘ri so‘rov"


def test_approving_a_payment_without_telegram_id_reports_it_in_chat(bot_db, client, admin_id):
    token = complete_session(client)
    assert client.post(f"/personality/result/{token}/support-bot", follow_redirects=False).status_code == 303
    with db_session(client) as db:
        payment_id = db.scalar(select(PaymentRequest)).id

    log = CallLog()
    run(
        handlers.cb_approve(
            make_callback(log, f"premium_approve:{payment_id}", user_id=admin_id), make_bot(log)
        )
    )

    assert log.last_text("callback_answer") == "Tasdiqlandi"
    assert "send_message" not in log.names()
    assert "Telegram ID si yo‘q" in log.last_text("answer")


# --------------------------------------------------------------------------- xato ishlovi va self-check


def test_error_handler_answers_the_user_and_swallows_the_exception(bot_db):
    log = CallLog()
    event = ErrorEvent(
        update=Update(update_id=1, message=make_message(log)),
        exception=RuntimeError("kutilmagan"),
    )
    assert run(handlers.on_unhandled_error(event)) is True
    assert log.last_text("answer") == handlers.ERROR_TEXT


def test_error_handler_answers_a_callback_query(bot_db):
    log = CallLog()
    event = ErrorEvent(
        update=Update(update_id=2, callback_query=make_callback(log, "premium_approve:1", user_id=1)),
        exception=RuntimeError("kutilmagan"),
    )
    assert run(handlers.on_unhandled_error(event)) is True
    assert log.last_text("callback_answer") == handlers.ERROR_TEXT


def test_configuration_self_check_reports_every_problem(monkeypatch):
    monkeypatch.setattr(settings, "admin_telegram_id", None)
    monkeypatch.setattr(settings, "bot_username", "boshqa_bot")
    monkeypatch.setattr(settings, "payment_support_bot_username", "")
    bot = AsyncMock()
    bot.get_me.return_value = SimpleNamespace(username="haqiqiy_bot")

    problems = run(handlers.check_bot_configuration(bot))

    assert any("ADMIN_TELEGRAM_ID" in problem for problem in problems)
    assert any("PUBLIC_BASE_URL" in problem for problem in problems)
    assert any("haqiqiy_bot" in problem for problem in problems)


def test_dispatcher_registers_the_router_and_error_handler():
    """aiogram routeri faqat bitta dispatcherga ulanadi — shuning uchun butun
    to'plamda create_dispatcher() aynan shu yerda bir marta chaqiriladi."""
    from app.bot import test_flow

    dispatcher = handlers.create_dispatcher()
    assert handlers.router in dispatcher.sub_routers
    # Test oqimi to'lov handlerlaridan oldin turishi kerak, aks holda /test va
    # javob callback'lari umumiy matn/fallback handleriga tushib ketadi.
    assert dispatcher.sub_routers.index(test_flow.router) < dispatcher.sub_routers.index(handlers.router)
    assert dispatcher.errors.handlers


def test_payment_id_parsing_rejects_garbage():
    assert handlers._payment_id_from_callback("premium_approve:12") == 12
    assert handlers._payment_id_from_callback("premium_approve:xy") is None
    assert handlers._payment_id_from_callback("premium_approve") is None
    assert handlers._payment_id_from_callback(None) is None


def test_fsm_payment_id_coercion_ignores_bools_and_junk():
    assert handlers._as_payment_id(5) == 5
    assert handlers._as_payment_id("5") == 5
    assert handlers._as_payment_id(True) is None
    assert handlers._as_payment_id("besh") is None
    assert handlers._as_payment_id(None) is None


def test_orphan_session_row_is_not_created_by_bot_tests(bot_db, client):
    """Bot testlari veb oqimidan tashqarida qator yaratmasligi kerak."""
    with db_session(client) as db:
        before = db.scalar(select(func.count()).select_from(PersonalityTestSession))
    log = CallLog()
    run(handlers.on_text(make_message(log, text="abcdefgh12345678"), make_state()))
    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PersonalityTestSession)) == before

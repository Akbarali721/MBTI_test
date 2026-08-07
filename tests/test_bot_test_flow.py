"""Botda to'liq test o'tkazish: sof oqim mantiqi va handlerlar."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.bot import test_flow
from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from tests.helpers import db_session

TELEGRAM_USER_ID = 4242


def _run_full_test(db, *, option_position: int = 0) -> test_flow._FinishedView:
    """Testni oxirigacha o'tkazadi va natija ko'rinishini qaytaradi."""
    view = test_flow.start_test(db, TELEGRAM_USER_ID, "male")
    finished = None
    for _ in range(100):
        option_id = view.option_ids[option_position if option_position >= 0 else -1]
        view, finished = test_flow.answer_question(db, view.token, option_id)
        if finished is not None:
            return finished
        assert view is not None
    raise AssertionError("test yakunlanmadi")


# --------------------------- oqim mantiqi ---------------------------


def test_start_test_creates_a_session_bound_to_the_telegram_user(client):
    with db_session(client) as db:
        view = test_flow.start_test(db, TELEGRAM_USER_ID, "male")
        session = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == view.token))

        assert session is not None
        assert session.telegram_user_id == TELEGRAM_USER_ID
        assert session.source == "telegram-bot"
        assert session.appearance_theme.value == "male"


def test_first_question_is_rendered_with_options(client):
    with db_session(client) as db:
        view = test_flow.start_test(db, TELEGRAM_USER_ID, "female")

    assert view.index == 0
    assert view.total >= 20
    assert len(view.option_ids) == len(view.option_texts) >= 2
    assert view.selected_option_id is None

    text = test_flow.format_question(view)
    assert f"Savol 1 / {view.total}" in text
    for letter, option_text in zip("ABCD", view.option_texts, strict=False):
        assert f"{letter}. {option_text}" in text


def test_answering_advances_to_the_next_question(client):
    with db_session(client) as db:
        first = test_flow.start_test(db, TELEGRAM_USER_ID, "male")
        second, finished = test_flow.answer_question(db, first.token, first.option_ids[0])

    assert finished is None
    assert second is not None
    assert second.index == 1
    assert second.question_id != first.question_id


def test_completing_every_question_finishes_the_session(client):
    with db_session(client) as db:
        finished = _run_full_test(db)
        session = db.scalar(
            select(PersonalityTestSession).where(PersonalityTestSession.token == finished.token)
        )

    assert session.status == PersonalitySessionStatus.COMPLETED
    assert len(finished.result_type) == 4
    assert finished.title
    assert finished.share_url.startswith("http")
    assert "/r/" in finished.share_url


def test_bot_result_matches_the_web_scoring(client):
    """Bot va veb bir xil ball hisoblashdan foydalanishi kerak."""
    from tests.helpers import complete_session, session_by_token

    web_token = complete_session(client, option_index=0)
    with db_session(client) as db:
        web_type = session_by_token(db, web_token).result_type
        bot_result = _run_full_test(db, option_position=0)

    assert bot_result.result_type == web_type


def test_opposite_answers_give_the_mirrored_type(client):
    with db_session(client) as db:
        first = _run_full_test(db, option_position=0)
        last = _run_full_test(db, option_position=-1)

    assert first.result_type != last.result_type
    for a, b in zip(first.result_type, last.result_type, strict=True):
        assert a != b


def test_stale_option_id_reshows_the_current_question(client):
    """Eski xabardagi tugma bosilsa oqim buzilmasligi kerak."""
    with db_session(client) as db:
        first = test_flow.start_test(db, TELEGRAM_USER_ID, "male")
        second, _ = test_flow.answer_question(db, first.token, first.option_ids[0])
        # Birinchi savolning varianti endi joriy emas.
        again, finished = test_flow.answer_question(db, first.token, first.option_ids[1])

    assert finished is None
    assert again is not None
    assert again.index == second.index


def test_answer_after_completion_returns_the_result(client):
    with db_session(client) as db:
        finished = _run_full_test(db)
        view, again = test_flow.answer_question(db, finished.token, 1)

    assert view is None
    assert again is not None
    assert again.result_type == finished.result_type


def test_resume_view_returns_the_current_question(client):
    with db_session(client) as db:
        first = test_flow.start_test(db, TELEGRAM_USER_ID, "male")
        test_flow.answer_question(db, first.token, first.option_ids[0])
        resumed = test_flow.resume_view(db, first.token)

    assert resumed is not None
    assert resumed.index == 1


def test_resume_view_is_none_after_completion(client):
    with db_session(client) as db:
        finished = _run_full_test(db)
        assert test_flow.resume_view(db, finished.token) is None


# --------------------------- klaviatura va matn ---------------------------


def test_question_keyboard_marks_the_selected_option(client):
    with db_session(client) as db:
        view = test_flow.start_test(db, TELEGRAM_USER_ID, "male")

    plain = test_flow.question_keyboard(view)
    assert [b.callback_data for b in plain.inline_keyboard[0]] == [
        f"{test_flow.OPTION_PREFIX}{option_id}" for option_id in view.option_ids
    ]
    assert not any("✅" in b.text for b in plain.inline_keyboard[0])

    chosen = type(view)(**{**view.__dict__, "selected_option_id": view.option_ids[1]})
    marked = test_flow.question_keyboard(chosen)
    assert marked.inline_keyboard[0][1].text.startswith("✅")


def test_result_keyboard_links_to_result_and_share(client):
    with db_session(client) as db:
        finished = _run_full_test(db)

    markup = test_flow.result_keyboard(finished)
    urls = [button.url for row in markup.inline_keyboard for button in row]
    assert finished.result_url in urls
    assert finished.share_url in urls


def test_gender_keyboard_offers_both_options():
    markup = test_flow.gender_keyboard()
    values = [b.callback_data for b in markup.inline_keyboard[0]]
    assert values == [f"{test_flow.GENDER_PREFIX}female", f"{test_flow.GENDER_PREFIX}male"]


# --------------------------- handlerlar ---------------------------


def test_test_command_asks_for_gender(client, monkeypatch):
    monkeypatch.setattr("app.bot.handlers.SessionLocal", client.testing_session_factory)
    message = AsyncMock()
    state = AsyncMock()
    state.get_data.return_value = {}

    asyncio.run(test_flow.cmd_test(message, state))

    message.answer.assert_awaited_once()
    assert test_flow.INTRO_TEXT in message.answer.await_args.args[0]


def test_gender_callback_starts_the_test(client, monkeypatch):
    monkeypatch.setattr("app.bot.handlers.SessionLocal", client.testing_session_factory)

    query = AsyncMock()
    query.data = f"{test_flow.GENDER_PREFIX}male"
    query.from_user.id = TELEGRAM_USER_ID
    query.message = _fake_message()
    state = AsyncMock()

    asyncio.run(test_flow.cb_gender(query, state, AsyncMock()))

    query.message.edit_text.assert_awaited_once()
    assert "Savol 1 /" in query.message.edit_text.await_args.args[0]
    state.update_data.assert_awaited()


def test_option_callback_without_a_token_explains_itself(client, monkeypatch):
    monkeypatch.setattr("app.bot.handlers.SessionLocal", client.testing_session_factory)

    query = AsyncMock()
    query.data = f"{test_flow.OPTION_PREFIX}1"
    query.message = _fake_message()
    state = AsyncMock()
    state.get_data.return_value = {}

    asyncio.run(test_flow.cb_option(query, state, AsyncMock()))

    query.message.answer.assert_awaited_once()
    assert test_flow.ABANDONED_TEXT in query.message.answer.await_args.args[0]


def test_option_callback_ignores_a_malformed_payload(client, monkeypatch):
    monkeypatch.setattr("app.bot.handlers.SessionLocal", client.testing_session_factory)

    query = AsyncMock()
    query.data = f"{test_flow.OPTION_PREFIX}abc"
    query.message = _fake_message()
    state = AsyncMock()
    state.get_data.return_value = {"token": "yoq"}

    asyncio.run(test_flow.cb_option(query, state, AsyncMock()))

    query.message.edit_text.assert_not_awaited()


def _fake_message():
    """isinstance(x, Message) dan o'tadi; aiogram metodlari sinxron e'lon qilingani
    uchun spec ularni MagicMock qiladi — kutiladiganlarini aniq almashtiramiz."""
    from aiogram.types import Message

    message = AsyncMock(spec=Message)
    message.edit_text = AsyncMock()
    message.answer = AsyncMock()
    return message


@pytest.fixture(autouse=True)
def _quiet_telegram(monkeypatch):
    """Handlerlar _safe_telegram orqali ishlaydi — u haqiqiy tarmoqqa chiqmasligi kerak."""

    async def _passthrough(action, coro):
        await coro
        return True

    monkeypatch.setattr("app.bot.handlers._safe_telegram", _passthrough)

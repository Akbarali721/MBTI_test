"""Test kodi: hosil qilish, toʻqnashuv va natija sahifasidagi toʻlov bloki."""

from sqlalchemy import func, select

from app.config import settings
from app.i18n import t
from app.models.enums import PersonalitySessionStatus
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityTestSession
from app.personality.payment_code import (
    find_sessions_by_payment_code,
    generate_payment_code,
    payment_code_for_session,
)
from tests.helpers import complete_session, db_session, session_by_token


def test_payment_code_for_completed_session(client):
    token = complete_session(client)
    with db_session(client) as db:
        row = session_by_token(db, token)
        code = payment_code_for_session(db, row)
        assert len(code) >= 8
        assert row.token.startswith(code)

        found = find_sessions_by_payment_code(db, code)
        assert len(found) == 1
        assert found[0].id == row.id


def test_payment_code_lookup_is_case_insensitive(client):
    token = complete_session(client)
    with db_session(client) as db:
        code = session_by_token(db, token).payment_code
        assert find_sessions_by_payment_code(db, f"  {code.upper()}  ")
        assert find_sessions_by_payment_code(db, "") == []


def test_payment_code_expands_on_collision(client):
    with db_session(client) as db:
        base = "0155ac4f"
        first = PersonalityTestSession(token=base + "a" * 24, status=PersonalitySessionStatus.COMPLETED)
        second = PersonalityTestSession(token=base + "b" * 24, status=PersonalitySessionStatus.COMPLETED)
        db.add_all([first, second])
        db.commit()
        db.refresh(first)
        db.refresh(second)

        first_code = payment_code_for_session(db, first)
        second_code = payment_code_for_session(db, second)
        assert first_code != second_code
        assert first.token.startswith(first_code)
        assert second.token.startswith(second_code)


def test_payment_code_generation_ignores_empty_token(client):
    with db_session(client) as db:
        assert generate_payment_code(db, "") == ""
        assert generate_payment_code(db, "   ") == ""


def test_result_support_bot_flow(client, monkeypatch):
    monkeypatch.setattr(settings, "payment_support_bot_username", "xarakter_test_support_bot")
    token = complete_session(client)

    page = client.get(f"/personality/result/{token}")
    assert 'id="payment-test-code"' in page.text
    assert 'target="_blank"' in page.text
    assert 'rel="noopener noreferrer"' in page.text

    # GET faqat yoʻnaltiradi, hech qanday toʻlov yozuvi yaratmaydi.
    redirect = client.get(f"/personality/result/{token}/support-bot", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"https://t.me/xarakter_test_support_bot?start=premium_{token}"

    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 0

    started = client.post(f"/personality/result/{token}/support-bot", follow_redirects=False)
    assert started.status_code == 303
    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1


def test_legacy_payment_telegram_post_still_starts_the_flow(client, monkeypatch):
    monkeypatch.setattr(settings, "payment_support_bot_username", "xarakter_test_support_bot")
    token = complete_session(client)

    legacy = client.post(f"/personality/result/{token}/payment-telegram", follow_redirects=False)
    assert legacy.status_code == 303
    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1


def test_support_bot_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "payment_support_bot_username", "")
    monkeypatch.setattr(settings, "bot_username", "")
    token = complete_session(client)

    page = client.get(f"/personality/result/{token}")
    assert "mbti-payment-unavailable" in page.text
    assert t("payment.unavailable", "uz") in page.text

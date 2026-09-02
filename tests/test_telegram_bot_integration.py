"""Telegram bot integratsiyasi testlari."""

from __future__ import annotations

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramReferral
from app.services.telegram_referral_service import (
    attribute_bot_referral,
    mark_referral_completed,
    parse_referral_telegram_id,
    sync_referral_to_session,
    telegram_referral_url,
)
from app.services.telegram_user_service import TelegramProfileInput, upsert_from_bot_start
from tests.helpers import complete_session, db_session, session_by_token


def test_parse_referral_telegram_id():
    assert parse_referral_telegram_id("ref_123456789") == 123456789
    assert parse_referral_telegram_id("premium_abc") is None
    assert parse_referral_telegram_id("ref_0") is None


def test_telegram_referral_url_uses_bot_username(monkeypatch):
    monkeypatch.setattr(
        "app.services.telegram_referral_service.settings.telegram_bot_username",
        "XarakterimBot",
    )
    assert telegram_referral_url(123) == "https://t.me/XarakterimBot?start=ref_123"


def test_bot_start_upserts_user(client):
    with db_session(client) as db:
        user = upsert_from_bot_start(
            db,
            TelegramProfileInput(
                telegram_id=999001,
                username="testuser",
                first_name="Akbar",
                last_name="Ali",
            ),
        )
        db.commit()
        assert user.telegram_id == 999001
        assert user.telegram_username == "testuser"
        assert user.bot_started_at is not None

        again = upsert_from_bot_start(
            db,
            TelegramProfileInput(telegram_id=999001, username="newname"),
        )
        db.commit()
        assert again.id == user.id
        assert again.telegram_username == "newname"


def test_self_referral_blocked(client):
    with db_session(client) as db:
        referred = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=100))
        db.flush()
        assert attribute_bot_referral(db, referred=referred, referrer_telegram_id=100) is False


def test_referral_unique_per_referred(client):
    with db_session(client) as db:
        upsert_from_bot_start(db, TelegramProfileInput(telegram_id=200, username="ref"))
        referred = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=201))
        other = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=202))
        db.flush()

        assert attribute_bot_referral(db, referred=referred, referrer_telegram_id=200) is True
        assert attribute_bot_referral(db, referred=referred, referrer_telegram_id=202) is False
        assert attribute_bot_referral(db, referred=other, referrer_telegram_id=200) is True
        db.commit()

        refs = db.query(TelegramReferral).all()
        assert len(refs) == 2


def test_sync_referral_to_session(client):
    referrer_token = complete_session(client)
    with db_session(client) as db:
        referrer_session = session_by_token(db, referrer_token)
        referrer_session.telegram_user_id = 300
        referrer = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=300))
        referred = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=301))
        db.flush()
        attribute_bot_referral(db, referred=referred, referrer_telegram_id=300)

        session = PersonalityTestSession(
            token="visitor-sync-ref",
            status=PersonalitySessionStatus.VISITED,
            telegram_user_id=301,
        )
        db.add(session)
        db.flush()

        assert sync_referral_to_session(db, tg_user=referred, session=session) is True
        assert session.referred_by_session_id == referrer_session.id


def test_mark_referral_completed(client):
    with db_session(client) as db:
        upsert_from_bot_start(db, TelegramProfileInput(telegram_id=400))
        referred = upsert_from_bot_start(db, TelegramProfileInput(telegram_id=401))
        db.flush()
        attribute_bot_referral(db, referred=referred, referrer_telegram_id=400)
        referred_id = referred.id
        db.commit()

    token = complete_session(client, open_result=False)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.telegram_user_id = 401
        session.status = PersonalitySessionStatus.COMPLETED
        db.flush()

        mark_referral_completed(db, session)
        db.commit()

        ref = db.query(TelegramReferral).filter_by(referred_telegram_user_id=referred_id).one()
        assert ref.completed_at is not None
        assert ref.referred_session_id == session.id

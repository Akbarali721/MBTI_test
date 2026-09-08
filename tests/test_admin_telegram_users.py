"""Admin Telegram foydalanuvchilari bo'limi testlari."""

from __future__ import annotations

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.services.telegram_referral_service import attribute_bot_referral
from app.services.telegram_user_service import TelegramProfileInput, upsert_from_bot_start
from tests.helpers import admin_login, db_session


def _seed_telegram_user(db, *, telegram_id: int, username: str | None = None) -> int:
    user = upsert_from_bot_start(
        db,
        TelegramProfileInput(
            telegram_id=telegram_id,
            username=username,
            first_name="Test",
        ),
    )
    db.flush()
    return user.id


def test_admin_telegram_users_list_and_detail(client):
    with db_session(client) as db:
        user_id = _seed_telegram_user(db, telegram_id=880001, username="tguser1")
        session = PersonalityTestSession(
            token="tg-admin-list",
            status=PersonalitySessionStatus.COMPLETED,
            telegram_user_id=880001,
            result_type="ESTP",
        )
        db.add(session)
        db.commit()

    admin_login(client)
    listing = client.get("/admin/telegram-users")
    assert listing.status_code == 200
    assert "Foydalanuvchilar" in listing.text
    assert "@tguser1" in listing.text
    assert "880001" in listing.text
    assert "ESTP" in listing.text
    assert "Botga kirganlar" in listing.text

    detail = client.get(f"/admin/telegram-users/{user_id}")
    assert detail.status_code == 200
    assert "@tguser1" in detail.text
    assert "ESTP" in detail.text


def test_admin_telegram_users_filters(client):
    with db_session(client) as db:
        _seed_telegram_user(db, telegram_id=880010, username="started")
        _seed_telegram_user(db, telegram_id=880011, username="completed")
        _seed_telegram_user(db, telegram_id=880012, username="onlybot")

        db.add(
            PersonalityTestSession(
                token="tg-started-real",
                status=PersonalitySessionStatus.IN_PROGRESS,
                telegram_user_id=880010,
            )
        )
        db.add(
            PersonalityTestSession(
                token="tg-completed",
                status=PersonalitySessionStatus.COMPLETED,
                telegram_user_id=880011,
                result_type="INFJ",
            )
        )
        db.commit()

    admin_login(client)

    started_page = client.get("/admin/telegram-users?filter=test_started")
    assert started_page.status_code == 200
    assert "@started" in started_page.text
    assert "@onlybot" not in started_page.text

    completed_page = client.get("/admin/telegram-users?filter=test_completed")
    assert completed_page.status_code == 200
    assert "@completed" in completed_page.text
    assert "@started" not in completed_page.text

    not_completed_page = client.get("/admin/telegram-users?filter=not_completed")
    assert not_completed_page.status_code == 200
    assert "@started" in not_completed_page.text
    assert "@completed" not in not_completed_page.text
    assert "@onlybot" not in not_completed_page.text


def test_admin_telegram_users_referred_filter_and_detail_invites(client):
    with db_session(client) as db:
        referrer = upsert_from_bot_start(
            db, TelegramProfileInput(telegram_id=880020, username="referrer")
        )
        referred = upsert_from_bot_start(
            db, TelegramProfileInput(telegram_id=880021, username="referred")
        )
        db.flush()
        attribute_bot_referral(db, referred=referred, referrer_telegram_id=880020)
        db.commit()
        referrer_id = referrer.id

    admin_login(client)

    referred_page = client.get("/admin/telegram-users?filter=referred")
    assert referred_page.status_code == 200
    assert "@referred" in referred_page.text

    detail = client.get(f"/admin/telegram-users/{referrer_id}")
    assert detail.status_code == 200
    assert "@referred" in detail.text


def test_admin_dashboard_shows_telegram_funnel(client):
    with db_session(client) as db:
        _seed_telegram_user(db, telegram_id=880030, username="dashuser")
        db.commit()

    admin_login(client)
    dash = client.get("/admin")
    assert dash.status_code == 200
    assert "Telegram foydalanuvchilar" in dash.text
    assert "Botga kirganlar" in dash.text
    assert "Premium olganlar" in dash.text

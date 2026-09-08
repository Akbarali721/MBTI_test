"""Kunlik analitika drill-down testlari."""

from __future__ import annotations

from sqlalchemy import select

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.services.admin_daily_drilldown_service import (
    METRIC_COMPLETED,
    METRIC_VISITED,
    AdminDailyDrilldownService,
)
from app.services.telegram_user_service import TelegramProfileInput, upsert_from_bot_start
from app.timeutils import TASHKENT_TZ, tashkent_day_start, utcnow
from tests.helpers import admin_login, complete_session, db_session, session_by_token


def _day_label(moment) -> str:
    return moment.astimezone(TASHKENT_TZ).strftime("%Y-%m-%d")


def test_daily_visited_drilldown_lists_sessions(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="instagram")
        day_label = _day_label(session.created_at)
        db.commit()

    admin_login(client)
    page = client.get(f"/admin/analytics/day?date={day_label}&metric=visited")
    assert page.status_code == 200
    assert day_label in page.text
    assert "instagram" in page.text


def test_daily_visited_unique_users(client):
    with db_session(client) as db:
        upsert_from_bot_start(db, TelegramProfileInput(telegram_id=770001, username="dupuser"))
        db.add(
            PersonalityTestSession(
                token="visit-a",
                status=PersonalitySessionStatus.VISITED,
                telegram_user_id=770001,
                source="bot",
            )
        )
        db.add(
            PersonalityTestSession(
                token="visit-b",
                status=PersonalitySessionStatus.VISITED,
                telegram_user_id=770001,
                source="bot",
            )
        )
        day_label = _day_label(tashkent_day_start())
        db.commit()

    with db_session(client) as db:
        report = AdminDailyDrilldownService(db).report(day_label=day_label, metric=METRIC_VISITED)
        assert report is not None
        assert report.total_sessions == 2
        assert report.unique_users == 1

    admin_login(client)
    page = client.get(f"/admin/analytics/day?date={day_label}&metric=visited")
    assert "@dupuser" in page.text
    assert "tashrif/sessiya" in page.text
    assert "unique foydalanuvchi" in page.text


def test_daily_anonymous_session_label(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="direct")
        day_label = _day_label(session.created_at)
        db.commit()

    with db_session(client) as db:
        report = AdminDailyDrilldownService(db).report(day_label=day_label, metric=METRIC_VISITED)
        assert report is not None
        assert report.rows[0].display_name == "Anonymous"
        assert report.rows[0].status_label == "Anonymous web visit"


def test_daily_completed_drilldown_by_completed_at(client):
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        now = utcnow()
        session.completed_at = now
        day_label = _day_label(now)
        db.commit()

    admin_login(client)
    page = client.get(f"/admin/analytics/day?date={day_label}&metric=completed")
    assert page.status_code == 200
    assert "Testni tugatdi" in page.text


def test_dashboard_daily_links_are_clickable(client):
    client.get("/personality?source=direct")
    admin_login(client)
    dash = client.get("/admin")
    assert dash.status_code == 200
    assert "/admin/analytics/day?date=" in dash.text
    assert "metric=visited" in dash.text

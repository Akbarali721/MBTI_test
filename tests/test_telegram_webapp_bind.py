"""Telegram WebApp sessiya bog'lanishi testlari."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramUser
from app.services.admin_daily_drilldown_service import METRIC_VISITED, AdminDailyDrilldownService
from app.timeutils import TASHKENT_TZ
from tests.helpers import db_session
from tests.test_telegram_webapp_auth import BOT_TOKEN, _signed_init_data


@pytest.fixture
def bot_token(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)
    monkeypatch.setattr(settings, "telegram_bot_token", BOT_TOKEN)


def test_telegram_bind_links_session_and_user(client, bot_token):
    client.get("/personality")
    init_data = _signed_init_data(
        {"id": 880100, "username": "webapp_user", "first_name": "Ali", "last_name": "Valiyev"}
    )
    response = client.post("/personality/telegram-bind", data={"init_data": init_data})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["telegram_user_id"] == 880100

    with db_session(client) as db:
        session = db.scalar(select(PersonalityTestSession))
        assert session is not None
        assert session.telegram_user_id == 880100
        assert session.telegram_username == "webapp_user"
        assert session.telegram_first_name == "Ali"
        assert session.telegram_last_name == "Valiyev"
        assert session.source == "telegram-webapp"

        tg_user = db.scalar(select(TelegramUser).where(TelegramUser.telegram_id == 880100))
        assert tg_user is not None
        assert tg_user.telegram_username == "webapp_user"


def test_telegram_bind_creates_session_when_cookie_missing(client, bot_token):
    init_data = _signed_init_data({"id": 880101, "username": "direct_bind", "first_name": "Zara"})
    response = client.post("/personality/telegram-bind", data={"init_data": init_data})
    assert response.status_code == 200
    assert response.json()["ok"] is True

    with db_session(client) as db:
        session = db.scalar(select(PersonalityTestSession))
        assert session is not None
        assert session.telegram_user_id == 880101
        assert session.telegram_username == "direct_bind"


def test_telegram_bind_shows_in_admin_daily_drilldown(client, bot_token):
    client.get("/personality")
    init_data = _signed_init_data({"id": 880102, "username": "analytics_user", "first_name": "Sara"})
    assert client.post("/personality/telegram-bind", data={"init_data": init_data}).status_code == 200

    with db_session(client) as db:
        session = db.scalar(select(PersonalityTestSession))
        day_label = session.created_at.astimezone(TASHKENT_TZ).strftime("%Y-%m-%d")
        report = AdminDailyDrilldownService(db).report(day_label=day_label, metric=METRIC_VISITED)
        assert report is not None
        assert report.rows[0].display_name == "@analytics_user"
        assert report.rows[0].telegram_id == 880102
        assert report.rows[0].first_name == "Sara"
        assert report.rows[0].status_label != "Anonymous web visit"

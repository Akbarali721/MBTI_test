"""Test progress tracking va funnel analitikasi testlari."""

from __future__ import annotations

from datetime import timedelta

from app.models.enums import PersonalitySessionStatus
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_service import PersonalityService
from app.services.test_funnel_analytics_service import SessionTestFunnelAnalyticsService
from app.timeutils import utcnow
from tests.helpers import admin_login, answer_question, db_session, session_by_token, start_session


def test_max_question_reached_does_not_decrease_when_navigating_back(client):
    client.get("/personality")
    token = start_session(client)

    for idx in range(12):
        answer_question(client, token, idx)

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.max_question_reached >= 12

    page = client.get(f"/personality/test/{token}?q=4")
    assert page.status_code == 200

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.max_question_reached >= 12
        assert session.current_question_number == 5


def test_last_answered_at_updated_on_answer(client):
    client.get("/personality")
    token = start_session(client)
    answer_question(client, token, 0)

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.last_answered_at is not None
        assert session.max_question_reached >= 1


def test_completed_session_sets_full_progress(client):
    client.get("/personality")
    token = start_session(client)
    for idx in range(24):
        answer_question(client, token, idx)

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.status == PersonalitySessionStatus.COMPLETED
        assert session.max_question_reached == 24
        assert session.current_question_number == 24


def test_test_funnel_milestones(client):
    client.get("/personality")
    token = start_session(client)
    for idx in range(10):
        answer_question(client, token, idx)

    admin_login(client)
    with db_session(client) as db:
        report = SessionTestFunnelAnalyticsService(db).report()
        counts = {stage.key: stage.count for stage in report.stages}
        assert counts["started"] >= 1
        assert counts["q10"] >= 1
        assert counts["q15"] == 0 or counts["q15"] < counts["q10"]


def test_question_drop_off_top5(client):
    client.get("/personality")
    token_a = start_session(client)
    for idx in range(3):
        answer_question(client, token_a, idx)

    client.get("/personality")
    token_b = start_session(client)
    for idx in range(8):
        answer_question(client, token_b, idx)

    with db_session(client) as db:
        report = SessionTestFunnelAnalyticsService(db).report()
        assert len(report.question_drop_offs) == 24
        assert len(report.top_drop_offs) <= 5
        assert all(row.drop_off_pct >= 0 for row in report.top_drop_offs)


def test_admin_dashboard_shows_test_funnel(client):
    client.get("/personality")
    token = start_session(client)
    answer_question(client, token, 0)

    admin_login(client)
    dash = client.get("/admin")
    assert dash.status_code == 200
    assert "Test funnel" in dash.text
    assert "TOP 5 chiqib ketish savollari" in dash.text or "1-savol" in dash.text


def test_admin_telegram_users_show_progress(client):
    from app.models.personality import PersonalityTestSession
    from app.services.telegram_user_service import TelegramProfileInput, upsert_from_bot_start

    with db_session(client) as db:
        user = upsert_from_bot_start(
            db, TelegramProfileInput(telegram_id=881001, username="proguser", first_name="Prog")
        )
        session = PersonalityTestSession(
            token="prog-session",
            status=PersonalitySessionStatus.IN_PROGRESS,
            telegram_user_id=881001,
            started_at=utcnow(),
            total_questions=24,
            max_question_reached=7,
            answered_questions=7,
            last_activity_at=utcnow(),
        )
        db.add(session)
        db.commit()
        user_id = user.id

    admin_login(client)
    page = client.get("/admin/telegram-users")
    assert page.status_code == 200
    assert "7 / 24" in page.text
    assert "Davom etmoqda" in page.text

    detail = client.get(f"/admin/telegram-users/{user_id}")
    assert detail.status_code == 200
    assert "7 / 24" in detail.text


def test_abandoned_progress_status(client):
    from app.models.personality import PersonalityTestSession
    from app.personality.test_progress import progress_status_label

    with db_session(client) as db:
        session = PersonalityTestSession(
            token="abandon-prog",
            status=PersonalitySessionStatus.IN_PROGRESS,
            started_at=utcnow() - timedelta(days=10),
            last_activity_at=utcnow() - timedelta(days=10),
            total_questions=24,
            max_question_reached=5,
        )
        db.add(session)
        db.commit()
        assert progress_status_label(session) == "Tashlab ketgan"

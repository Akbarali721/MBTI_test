"""Saqlash siyosati: nima o'chiriladi, nima ASLO o'chirilmaydi."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.config import settings
from app.models.admin import AdminAuditLog
from app.models.analytics import SessionDailyStats
from app.models.enums import NotificationStatus, PersonalitySessionStatus
from app.models.notification import NotificationOutbox
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityAnswer, PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.retention import __main__ as retention_cli
from app.services import notification_outbox as outbox
from app.services import retention_service
from app.services.admin_analytics_service import AdminAnalyticsService
from app.services.premium_payment_service import PremiumPaymentService
from app.timeutils import utcnow
from tests.helpers import admin_login, complete_session, db_session, session_by_token


@pytest.fixture()
def retention_db(client, monkeypatch):
    """CLI o'z sessiyasini `SessionLocal` orqali ochadi — uni test bazasiga qaratamiz."""
    monkeypatch.setattr(retention_cli, "SessionLocal", client.testing_session_factory)
    return client


def _age(client, token: str, days: int) -> None:
    with db_session(client) as db:
        session = session_by_token(db, token)
        moment = utcnow() - timedelta(days=days)
        session.created_at = moment
        session.last_activity_at = moment
        db.commit()


def _make_visited(client, *, days: int, source: str = "eski") -> int:
    with db_session(client) as db:
        session = PersonalityRepository(db).create_session(source=source)
        moment = utcnow() - timedelta(days=days)
        session.created_at = moment
        session.last_activity_at = moment
        db.commit()
        return session.id


def _count(client, model) -> int:
    with db_session(client) as db:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _apply(client, **kwargs):
    with db_session(client) as db:
        return retention_service.run(db, dry_run=False, **kwargs)


# --------------------------------------------------------------------------- xavfsizlik


def test_zero_days_means_disabled_not_delete_everything(client, monkeypatch):
    """Sozlamada "0" o'chirilgan degani; eski kod uni "hozirgacha hammasi" deb tushunardi."""
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 0)

    report = _apply(client, rules=["visited"])
    rule = report.rules[0]
    assert rule.enabled is False
    assert rule.affected == 0
    assert _count(client, PersonalityTestSession) == 1


def test_the_repository_refuses_a_zero_day_purge(client):
    with db_session(client) as db:
        with pytest.raises(ValueError):
            PersonalityRepository(db).delete_stale_visited_sessions(older_than_days=0)
        with pytest.raises(ValueError):
            PersonalityRepository(db).delete_stale_visited_sessions(older_than_days=-1)


def test_a_negative_retention_setting_is_refused_at_load_time():
    from app.config import Settings

    with pytest.raises(ValueError):
        Settings(
            secret_key="x" * 40,
            debug=True,
            admin_password_hash="hash",
            retention_visited_days=-1,
        )


def test_a_session_with_a_payment_is_never_deleted(client, monkeypatch):
    """Sessiyani o'chirish TO'LOV QATORINI ham kaskad bilan olib ketardi."""
    token = complete_session(client)
    with db_session(client) as db:
        PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=333,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
    # Sessiyani VISITED holatiga majburan qaytaramiz — eng yomon holat.
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.status = PersonalitySessionStatus.VISITED
        session.completed_at = None
        session.result_type = None
        session.premium_requested = False
        session.premium_requested_at = None
        db.commit()
    _age(client, token, 400)

    monkeypatch.setattr(settings, "retention_visited_days", 30)
    report = _apply(client, rules=["visited"])

    assert report.rules[0].affected == 0
    assert _count(client, PaymentRequest) == 1
    assert _count(client, PersonalityTestSession) == 1


def test_a_session_in_a_team_is_never_deleted(client, monkeypatch):
    from app.services.team_service import add_member, create_team

    token = complete_session(client)
    with db_session(client) as db:
        team = create_team(db, "Jamoa")
        add_member(db, team, session_by_token(db, token), "Dilnoza")
        db.commit()
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.status = PersonalitySessionStatus.VISITED
        session.completed_at = None
        session.result_type = None
        db.commit()
    _age(client, token, 400)

    monkeypatch.setattr(settings, "retention_visited_days", 30)
    assert _apply(client, rules=["visited"]).rules[0].affected == 0
    assert _count(client, PersonalityTestSession) == 1


def test_a_premium_session_is_never_touched(client, monkeypatch):
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.is_premium = True
        session.status = PersonalitySessionStatus.IN_PROGRESS
        session.completed_at = None
        session.result_type = None
        db.commit()
    _age(client, token, 400)

    monkeypatch.setattr(settings, "retention_incomplete_days", 90)
    assert _apply(client, rules=["incomplete"]).rules[0].affected == 0
    with db_session(client) as db:
        assert session_by_token(db, token).anonymized_at is None


# --------------------------------------------------------------------------- o'chirish va agregat


def test_stale_visited_sessions_are_deleted(client, monkeypatch):
    _make_visited(client, days=400)
    _make_visited(client, days=1)
    monkeypatch.setattr(settings, "retention_visited_days", 30)

    report = _apply(client, rules=["visited"])
    assert report.rules[0].affected == 1
    assert _count(client, PersonalityTestSession) == 1


def test_deleting_sessions_does_not_rewrite_the_funnel(client, monkeypatch):
    """Tozalash faqat MAXRAJNI kamaytirsa, tugatish foizi sun'iy ko'tarilardi."""
    complete_session(client)
    for _ in range(3):
        _make_visited(client, days=400)

    with db_session(client) as db:
        before = AdminAnalyticsService(db).dashboard_stats()
        before_funnel = [stage.count for stage in AdminAnalyticsService(db).funnel(days=None).stages]

    monkeypatch.setattr(settings, "retention_visited_days", 30)
    assert _apply(client, rules=["visited"]).rules[0].affected == 3

    with db_session(client) as db:
        after = AdminAnalyticsService(db).dashboard_stats()
        after_funnel = [stage.count for stage in AdminAnalyticsService(db).funnel(days=None).stages]
        archived = db.scalar(select(func.sum(SessionDailyStats.visited)))

    assert archived == 3
    assert after.total_visitors == before.total_visitors
    assert after.completion_rate == before.completion_rate
    assert after_funnel == before_funnel


def test_the_rollup_groups_by_tashkent_day_not_utc_day(client, monkeypatch):
    """Toshkentda 02:00 — bu allaqachon KEYINGI kun (UTC 21:00).

    Kunni UTC bo'yicha bo'lish 00:00-05:00 oralig'idagi tashrifni oldingi kunga
    tushirib, dashboard'dagi "bugun" soni bilan ziddiyat chiqarardi.
    """
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        for hour in (3, 21):
            row = repo.create_session(source="kun")
            moment = (utcnow() - timedelta(days=40)).replace(hour=hour, minute=0, microsecond=0)
            row.created_at = moment
            row.last_activity_at = moment
        db.commit()

    monkeypatch.setattr(settings, "retention_visited_days", 30)
    assert _apply(client, rules=["visited"]).rules[0].affected == 2

    with db_session(client) as db:
        rows = db.execute(
            select(SessionDailyStats.day, SessionDailyStats.visited).order_by(SessionDailyStats.day)
        ).all()
    assert len(rows) == 2, "ikki xil Toshkent kuni ikkita qator bo'lishi kerak"
    assert [row[1] for row in rows] == [1, 1]
    assert (rows[1][0] - rows[0][0]) == timedelta(days=1)


def test_sessions_on_one_day_collapse_into_a_single_rollup_row(client, monkeypatch):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        for minute in (5, 25, 45):
            row = repo.create_session(source="kun")
            moment = (utcnow() - timedelta(days=40)).replace(hour=6, minute=minute, microsecond=0)
            row.created_at = moment
            row.last_activity_at = moment
        db.commit()

    monkeypatch.setattr(settings, "retention_visited_days", 30)
    _apply(client, rules=["visited"])

    with db_session(client) as db:
        rows = db.execute(select(SessionDailyStats.day, SessionDailyStats.visited)).all()
    assert len(rows) == 1
    assert rows[0][1] == 3


def test_a_second_run_does_not_inflate_the_rollup(client, monkeypatch):
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 30)

    assert _apply(client, rules=["visited"]).rules[0].affected == 1
    assert _apply(client, rules=["visited"]).rules[0].affected == 0

    with db_session(client) as db:
        assert db.scalar(select(func.sum(SessionDailyStats.visited))) == 1


# --------------------------------------------------------------------------- anonimlashtirish


def test_an_abandoned_session_is_anonymised_not_deleted(client, monkeypatch):
    from tests.helpers import answer_question, start_session

    token = start_session(client)
    answer_question(client, token, 0)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.telegram_user_id = 9999
        session.telegram_username = "abandoned"
        db.commit()
    _age(client, token, 200)

    monkeypatch.setattr(settings, "retention_incomplete_days", 90)
    report = _apply(client, rules=["incomplete"])
    assert report.rules[0].affected == 1

    with db_session(client) as db:
        # Qator qoladi — voronka tarixi buzilmaydi.
        session = db.scalar(select(PersonalityTestSession))
        assert session is not None
        assert session.anonymized_at is not None
        assert session.telegram_user_id is None
        assert session.telegram_username is None
        assert session.payment_code is None
        assert session.share_code is None
        assert session.token != token
        assert db.scalar(select(func.count()).select_from(PersonalityAnswer)) == 0
        assert session.status == PersonalitySessionStatus.STARTED


def test_anonymising_is_idempotent(client, monkeypatch):
    from tests.helpers import answer_question, start_session

    token = start_session(client)
    answer_question(client, token, 0)
    _age(client, token, 200)
    monkeypatch.setattr(settings, "retention_incomplete_days", 90)

    assert _apply(client, rules=["incomplete"]).rules[0].affected == 1
    assert _apply(client, rules=["incomplete"]).rules[0].affected == 0


# --------------------------------------------------------------------------- navbat va audit


def test_undelivered_notifications_survive_any_age(client, monkeypatch):
    """Yuborilmagan xabar — "mijozga aytilmagan" degan yagona dalil."""
    with db_session(client) as db:
        for index, status in enumerate(
            (NotificationStatus.PENDING, NotificationStatus.SENDING, NotificationStatus.SENT)
        ):
            outbox.enqueue(db, kind="user_approved", chat_id=1, params={}, key=f"k{index}")
            db.flush()
            row = db.scalars(select(NotificationOutbox).order_by(NotificationOutbox.id.desc())).first()
            row.status = status.value
            row.created_at = utcnow() - timedelta(days=400)
            if status is NotificationStatus.SENT:
                row.finished_at = utcnow() - timedelta(days=400)
        db.commit()

    monkeypatch.setattr(settings, "retention_outbox_days", 30)
    assert _apply(client, rules=["outbox"]).rules[0].affected == 1

    with db_session(client) as db:
        remaining = {row.status for row in db.scalars(select(NotificationOutbox)).all()}
    assert remaining == {NotificationStatus.PENDING.value, NotificationStatus.SENDING.value}


def test_money_related_audit_rows_are_never_purged(client, monkeypatch):
    with db_session(client) as db:
        for action in ("payment_approved", "login_success"):
            db.add(
                AdminAuditLog(
                    actor_type="web",
                    actor_label="test",
                    action=action,
                    created_at=utcnow() - timedelta(days=900),
                )
            )
        db.commit()

    monkeypatch.setattr(settings, "retention_audit_days", 1)
    _apply(client, rules=["audit"])

    with db_session(client) as db:
        actions = {row.action for row in db.scalars(select(AdminAuditLog)).all()}
    assert "payment_approved" in actions
    assert "login_success" not in actions


def test_an_applied_run_is_audited(client, monkeypatch):
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 30)
    _apply(client, rules=["visited"])

    with db_session(client) as db:
        entry = db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "retention_run"))
    assert entry is not None
    assert "visited=1/1" in entry.detail


# --------------------------------------------------------------------------- CLI va panel


def test_the_cli_defaults_to_a_dry_run(retention_db, client, capsys, monkeypatch):
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 30)

    assert retention_cli.main([]) == 0
    output = capsys.readouterr().out
    assert "HISOBOT" in output
    assert _count(client, PersonalityTestSession) == 1

    assert retention_cli.main(["--apply", "--rule", "visited"]) == 0
    assert "BAJARILDI" in capsys.readouterr().out
    assert _count(client, PersonalityTestSession) == 0


def test_the_cli_prints_the_resolved_cutoff(retention_db, client, capsys, monkeypatch):
    """ "30 kun" dan yurishni qayta tiklab bo'lmaydi — aniq chegara chop etiladi."""
    monkeypatch.setattr(settings, "retention_visited_days", 30)
    retention_cli.main([])
    assert str(utcnow().year) in capsys.readouterr().out


def test_the_admin_page_only_reports(client, monkeypatch):
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 30)
    admin_login(client)

    page = client.get("/admin/retention")
    assert page.status_code == 200
    assert "hech narsani o‘chirmaydi" in page.text
    assert "python -m app.retention --apply" in page.text
    # Sahifa ochilishi hech narsani o'chirmasligi kerak.
    assert _count(client, PersonalityTestSession) == 1


def test_the_legacy_purge_command_also_writes_the_rollup(client):
    """`python -m app.seed --purge-visited` ham agregatni yozishi shart.

    Ikkinchi, mustaqil o'chirish yo'li bo'lsa, u agregat qadamini jimgina o'tkazib
    yuborib voronka tarixini yo'q qilardi. Endi u ham saqlash siyosati xizmatidan
    o'tadi, ya'ni o'chirish yo'li bitta.
    """
    complete_session(client)
    for _ in range(2):
        _make_visited(client, days=400)

    with db_session(client) as db:
        before = AdminAnalyticsService(db).dashboard_stats().total_visitors
        removed = PersonalityRepository(db).delete_stale_visited_sessions(older_than_days=30)
        db.commit()

    assert removed == 2
    with db_session(client) as db:
        assert db.scalar(select(func.sum(SessionDailyStats.visited))) == 2
        assert AdminAnalyticsService(db).dashboard_stats().total_visitors == before


def test_the_purge_command_respects_its_days_argument(client, monkeypatch):
    """`--days` sozlamadagi muddatdan ustun turishi kerak."""
    _make_visited(client, days=10)
    monkeypatch.setattr(settings, "retention_visited_days", 365)

    with db_session(client) as db:
        assert PersonalityRepository(db).delete_stale_visited_sessions(older_than_days=5) == 1
        db.commit()
    assert _count(client, PersonalityTestSession) == 0


def test_the_dry_run_counts_without_materialising_ids(client, monkeypatch):
    """Hisobot admin sahifasida ochiladi — u yerda yuz minglab ID ni tortib olmaslik kerak."""
    _make_visited(client, days=400)
    monkeypatch.setattr(settings, "retention_visited_days", 30)

    called = []
    original = retention_service.stale_visited_ids

    def spy(*args, **kwargs):
        called.append(kwargs.get("limit"))
        return original(*args, **kwargs)

    monkeypatch.setattr(retention_service, "stale_visited_ids", spy)
    with db_session(client) as db:
        report = retention_service.run(db, dry_run=True, rules=["visited"])

    assert report.rules[0].candidates == 1
    assert called == [], "quruq hisobot ID ro'yxatini so'ramasligi kerak"


def test_a_session_with_a_free_trial_is_never_touched(client):
    """Referal mukofoti bergan vaqtli premium ham himoya belgisi."""
    from datetime import datetime, timedelta, timezone

    from app.services import retention_service

    with db_session(client) as db:
        session = PersonalityRepository(db).create_session()
        session.last_activity_at = datetime.now(timezone.utc) - timedelta(days=400)
        session.premium_until = datetime.now(timezone.utc) + timedelta(days=3)
        db.commit()
        session_id = session.id

        report = retention_service.run(db, dry_run=False, rules=[retention_service.RULE_VISITED])
        assert report.total_affected == 0
        assert db.get(PersonalityTestSession, session_id) is not None

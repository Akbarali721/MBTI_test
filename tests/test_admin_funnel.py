"""Voronka: kogorta, monotonlik va Toshkent kun chegarasi."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.services.admin_analytics_service import STAGE_KEYS, AdminAnalyticsService
from app.services.premium_payment_service import PremiumPaymentService
from app.timeutils import tashkent_day_start, utcnow
from tests.helpers import admin_login, complete_session, db_session, session_by_token


def _funnel(client, **kwargs):
    with db_session(client) as db:
        return AdminAnalyticsService(db).funnel(**kwargs)


def _counts(report) -> dict[str, int]:
    return {stage.key: stage.count for stage in report.stages}


def _open_payment(client, token: str, telegram_user_id: int = 900):
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=telegram_user_id,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
        assert outcome.payment is not None
        return outcome.payment.id


def _send_receipt(client, telegram_user_id: int, payment_id: int) -> None:
    with db_session(client) as db:
        PremiumPaymentService(db).attach_receipt(
            telegram_user_id=telegram_user_id,
            receipt_file_id="file",
            receipt_type="photo",
            payment_id=payment_id,
        )


def test_stages_are_never_non_monotonic(client):
    token = complete_session(client)
    payment_id = _open_payment(client, token)
    _send_receipt(client, 900, payment_id)
    with db_session(client) as db:
        PremiumPaymentService(db).approve_payment(payment_id, approved_by="test")

    report = _funnel(client, days=None)
    counts = [stage.count for stage in report.stages]
    assert counts == sorted(counts, reverse=True), counts
    assert _counts(report)["approved"] == 1
    assert all(stage.of_previous <= 100.0 for stage in report.stages)


def test_a_session_outside_the_window_is_excluded_at_every_stage(client):
    """Kogorta BIRINCHI tashrif kuni bo'yicha.

    Bosqichlarni o'z vaqti bo'yicha filtrlash 40 kun oldingi, kecha tasdiqlangan
    to'lovni "tasdiqlangan: 1, tashrif: 0" ko'rinishida chiqarardi.
    """
    token = complete_session(client)
    payment_id = _open_payment(client, token)
    _send_receipt(client, 900, payment_id)
    with db_session(client) as db:
        PremiumPaymentService(db).approve_payment(payment_id, approved_by="test")
        session = session_by_token(db, token)
        session.created_at = utcnow() - timedelta(days=40)
        db.commit()

    recent = _funnel(client, days=7)
    assert all(stage.count == 0 for stage in recent.stages)
    assert all(stage.of_first == 0.0 for stage in recent.stages)

    wide = _funnel(client, days=60)
    assert _counts(wide)["approved"] == 1
    assert _counts(wide)["visited"] == 1


def test_a_resent_receipt_does_not_double_count_the_session(client):
    """Rad etilgan chekdan keyin yangisi yangi TO'LOV QATORI yaratadi."""
    token = complete_session(client)
    payment_id = _open_payment(client, token, telegram_user_id=901)
    _send_receipt(client, 901, payment_id)
    with db_session(client) as db:
        PremiumPaymentService(db).reject_payment(payment_id, approved_by="test")
    _send_receipt(client, 901, payment_id)

    with db_session(client) as db:
        from app.models.payment_request import PaymentRequest

        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 2

    counts = _counts(_funnel(client, days=None))
    assert counts["visited"] == 1
    assert counts["receipt_sent"] == 1


def test_a_manual_grant_stays_monotonic_and_is_reported_as_an_anomaly(client):
    token = complete_session(client)
    admin_login(client)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
    client.post(f"/admin/personality/{session_id}/grant-premium")

    report = _funnel(client, days=None)
    counts = _counts(report)
    assert counts["approved"] == 1
    # Suffiks yig'indi tufayli chuqurroq bosqich hech qachon yuqoridagidan katta bo'lmaydi.
    assert counts["payment_started"] >= counts["approved"]
    assert report.premium_without_payment == 1


def test_a_legacy_row_without_started_at_still_counts_as_started(client):
    """003 migratsiyasi `started_at` ni backfill'siz qo'shgan edi."""
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.started_at = None
        db.commit()

    counts = _counts(_funnel(client, days=None))
    assert counts["started"] == 1
    assert counts["completed"] == 1


def test_the_daily_rows_sum_to_the_summary(client):
    complete_session(client)
    with db_session(client) as db:
        for _ in range(2):
            PersonalityRepository(db).create_session(source="test")
        db.commit()

    report = _funnel(client, days=14)
    for index, key in enumerate(STAGE_KEYS):
        assert sum(day.counts[index] for day in report.days) == report.stages[index].count, key


def test_the_newest_bucket_uses_the_tashkent_day_boundary(client):
    complete_session(client)
    report = _funnel(client, days=14)
    newest = report.days[-1]
    assert newest.day == tashkent_day_start()
    assert newest.visited == 1

    with db_session(client) as db:
        today = AdminAnalyticsService(db).dashboard_stats().today_visitors
    assert newest.visited == today


def test_an_empty_database_renders_without_dividing_by_zero(client):
    report = _funnel(client, days=30)
    assert report.total == 0
    assert all(stage.of_first == 0.0 and stage.of_previous == 0.0 for stage in report.stages)

    admin_login(client)
    assert client.get("/admin?range=30").status_code == 200


def test_the_dashboard_shows_the_funnel(client):
    complete_session(client)
    admin_login(client)
    page = client.get("/admin?range=7")
    assert page.status_code == 200
    assert "Voronka" in page.text
    assert "Test tugatildi" in page.text


def test_the_funnel_can_be_sliced_by_variant(client):
    complete_session(client)
    with db_session(client) as db:
        db.execute(
            select(PersonalityTestSession).where(
                PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED
            )
        )
        session = db.scalars(select(PersonalityTestSession)).first()
        session.variant = "B"
        db.commit()

    assert _counts(_funnel(client, days=None, variant="B"))["visited"] == 1
    assert _counts(_funnel(client, days=None, variant="A"))["visited"] == 0


def test_the_daily_table_never_shows_days_outside_the_window(client):
    """7 kunlik filtrda 14 kunlik jadval chizilsa, oyna tashqarisidagi kun nol ko'rinardi.

    Ya'ni haqiqatan tashrif bo'lgan kun "nol" deb o'qilardi.
    """
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        old = repo.create_session(source="eski")
        old.created_at = utcnow() - timedelta(days=10)
        old.last_activity_at = old.created_at
        repo.create_session(source="yangi")
        db.commit()

    wide = _funnel(client, days=30)
    assert len(wide.days) == 14
    assert sum(day.visited for day in wide.days) == 2

    narrow = _funnel(client, days=7)
    assert len(narrow.days) == 7
    # Oynada faqat bugungi sessiya bor va jadval yig'indisi umumiy songa teng.
    assert sum(day.visited for day in narrow.days) == narrow.stages[0].count == 1

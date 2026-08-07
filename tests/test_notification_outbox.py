"""Bildirishnoma navbati: tranzaksiya, band qilish, xato taksonomiyasi va yetkazish."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramConflictError,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.methods import SendMessage
from sqlalchemy import select

from app.bot import outbox_worker
from app.config import settings
from app.models.enums import NotificationStatus
from app.models.notification import OUTBOX_WORKER_HEARTBEAT, NotificationOutbox
from app.services import notification_outbox as outbox
from app.services.notification_outbox import (
    ADMIN_RECEIPT,
    PREMIUM_PDF,
    USER_APPROVED,
    USER_REJECTED,
)
from app.services.premium_payment_service import PremiumPaymentService
from app.timeutils import as_utc, utcnow
from tests.helpers import admin_login, complete_session, db_session, session_by_token


def run(coro):
    return asyncio.run(coro)


def _rows(client, **filters) -> list[NotificationOutbox]:
    with db_session(client) as db:
        stmt = select(NotificationOutbox).order_by(NotificationOutbox.id)
        for key, value in filters.items():
            stmt = stmt.where(getattr(NotificationOutbox, key) == value)
        return list(db.scalars(stmt).all())


def _paid_session(client, telegram_user_id: int = 555) -> tuple[str, int]:
    token = complete_session(client)
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=telegram_user_id,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
        payment_id = outcome.payment.id
        PremiumPaymentService(db).attach_receipt(
            telegram_user_id=telegram_user_id,
            receipt_file_id="file",
            receipt_type="photo",
            payment_id=payment_id,
        )
    return token, payment_id


def _enqueue_one(client, *, kind: str = USER_APPROVED, session_id: int = 1) -> int:
    with db_session(client) as db:
        outbox.enqueue(
            db,
            kind=kind,
            chat_id=555,
            params={"session_id": session_id, "payment_id": session_id},
            key=f"{kind}:test:{session_id}",
        )
        db.commit()
        row = db.scalar(select(NotificationOutbox).order_by(NotificationOutbox.id.desc()))
        return row.id


# --------------------------------------------------------------------------- ishlab chiqaruvchilar


def test_the_web_panel_approval_now_notifies_the_customer(client):
    """Avval veb paneldan tasdiqlash mijozga UMUMAN xabar bermasdi."""
    token, payment_id = _paid_session(client)
    admin_login(client)

    client.post(f"/admin/premium-requests/{payment_id}/approve")

    kinds = {row.kind for row in _rows(client)}
    assert {USER_APPROVED, PREMIUM_PDF} <= kinds
    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is True


def test_a_rejection_queues_the_rejection_message(client):
    _token, payment_id = _paid_session(client, telegram_user_id=556)
    admin_login(client)

    client.post(f"/admin/premium-requests/{payment_id}/reject")
    assert any(row.kind == USER_REJECTED for row in _rows(client))


def test_a_manual_grant_is_no_longer_silent(client):
    """Qo'lda ochilgan premium ham mijozga yetib borishi kerak."""
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.telegram_user_id = 4242
        session_id = session.id
        db.commit()
    admin_login(client)

    client.post(f"/admin/personality/{session_id}/grant-premium")
    kinds = {row.kind for row in _rows(client)}
    assert {USER_APPROVED, PREMIUM_PDF} <= kinds


def test_the_enqueue_shares_the_state_change_transaction(client, monkeypatch):
    """Navbat yozuvi buzilsa, to'lov ham tasdiqlanmasligi kerak."""
    token, payment_id = _paid_session(client, telegram_user_id=557)

    def boom(*_args, **_kwargs):
        raise RuntimeError("navbat ishlamadi")

    monkeypatch.setattr("app.services.premium_payment_service.enqueue", boom)
    with db_session(client) as db, pytest.raises(RuntimeError):
        PremiumPaymentService(db).approve_payment(payment_id, approved_by="test")

    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is False


def test_a_duplicate_key_does_not_abort_the_approval(client):
    """Takroriy kalit IntegrityError bersa, u tasdiqlashni ham orqaga qaytarardi."""
    token, _payment_id = _paid_session(client, telegram_user_id=558)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        for _ in range(2):
            outbox.enqueue(
                db,
                kind=USER_APPROVED,
                chat_id=558,
                params={"session_id": session_id},
                key="bir-xil-kalit",
            )
        db.commit()

    assert len(_rows(client, dedup_key="bir-xil-kalit")) == 1


# --------------------------------------------------------------------------- band qilish


def test_only_one_worker_can_claim_a_row(client):
    row_id = _enqueue_one(client)
    with db_session(client) as first, db_session(client) as second:
        claimed_first = outbox.claim_batch(first, worker_id="a", limit=10)
        claimed_second = outbox.claim_batch(second, worker_id="b", limit=10)

    assert claimed_first == [row_id]
    assert claimed_second == []
    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).attempts == 1


def test_a_stale_lease_is_reclaimed_but_a_live_one_is_not(client):
    stale_id = _enqueue_one(client, session_id=1)
    live_id = _enqueue_one(client, session_id=2)
    with db_session(client) as db:
        outbox.claim_batch(db, worker_id="dead", limit=10)
        db.get(NotificationOutbox, stale_id).lease_expires_at = utcnow() - timedelta(minutes=5)
        db.commit()

        assert outbox.reclaim_stale(db) == 1
        assert db.get(NotificationOutbox, stale_id).status == NotificationStatus.PENDING.value
        assert db.get(NotificationOutbox, live_id).status == NotificationStatus.SENDING.value


def test_a_row_scheduled_for_later_is_not_claimed(client):
    row_id = _enqueue_one(client)
    with db_session(client) as db:
        db.get(NotificationOutbox, row_id).next_attempt_at = utcnow() + timedelta(hours=1)
        db.commit()
        assert outbox.claim_batch(db, worker_id="a", limit=10) == []


# --------------------------------------------------------------------------- xato taksonomiyasi


def _telegram_error(exc_class):
    method = SendMessage(chat_id=1, text="x")
    if exc_class is TelegramRetryAfter:
        return TelegramRetryAfter(method=method, message="flood", retry_after=42)
    return exc_class(method=method, message="xato")


TAXONOMY = [
    (TelegramForbiddenError, NotificationStatus.BLOCKED.value),
    (TelegramBadRequest, NotificationStatus.FAILED.value),
    (TelegramNetworkError, NotificationStatus.PENDING.value),
    (TelegramServerError, NotificationStatus.PENDING.value),
]


@pytest.mark.parametrize(("exc_class", "expected"), TAXONOMY)
def test_each_telegram_error_maps_to_the_right_outcome(client, exc_class, expected):
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(exc_class)

    factory = client.testing_session_factory
    with db_session(client) as db:
        outbox.claim_batch(db, worker_id="w", limit=10)
    run(outbox_worker.deliver_one(bot, factory, row_id))

    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).status == expected


def test_a_flood_limit_is_honoured_without_burning_the_retry_budget(client):
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramRetryAfter)

    factory = client.testing_session_factory
    with db_session(client) as db:
        outbox.claim_batch(db, worker_id="w", limit=10)
    run(outbox_worker.deliver_one(bot, factory, row_id))

    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        # Telegram "42 soniya kuting" dedi — o'zimizning 30 soniyalik qadamimiz emas.
        delay = (as_utc(row.next_attempt_at) - utcnow()).total_seconds()
        assert 35 < delay < 60
        assert row.attempts == 0


def test_a_bad_token_does_not_burn_the_whole_queue(client):
    """TelegramUnauthorizedError — qatorning emas, JARAYONNING muammosi."""
    session_id = _premium_session_id(client)
    ids = [_enqueue_one(client, kind=USER_APPROVED, session_id=session_id) for _ in range(2)]
    for index, row_id in enumerate(ids):
        with db_session(client) as db:
            db.get(NotificationOutbox, row_id).dedup_key = f"unique-{index}"
            db.commit()

    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramUnauthorizedError)
    with pytest.raises(outbox_worker.ProcessLevelError):
        run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        statuses = {db.get(NotificationOutbox, row_id).status for row_id in ids}
    assert statuses == {NotificationStatus.PENDING.value}


def test_a_conflicting_second_bot_is_also_process_level(client):
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramConflictError)
    with pytest.raises(outbox_worker.ProcessLevelError):
        run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))
    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).status == NotificationStatus.PENDING.value


def test_retries_are_exhausted_into_failed(client):
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    with db_session(client) as db:
        db.get(NotificationOutbox, row_id).max_attempts = 1
        db.commit()

    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramNetworkError)
    run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).status == NotificationStatus.FAILED.value


# --------------------------------------------------------------------------- yetkazish


def _premium_session_id(client) -> int:
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.is_premium = True
        db.commit()
        return session.id


def test_a_successful_send_marks_the_row_sent(client):
    session_id = _premium_session_id(client)
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=session_id)

    bot = AsyncMock()
    sent = run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    assert sent == 1
    bot.send_message.assert_awaited_once()
    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        assert row.status == NotificationStatus.SENT.value
        assert row.finished_at is not None


def test_a_contradicted_message_is_cancelled_instead_of_lying(client):
    """Admin avval rad etib, keyin tasdiqlasa, kechikkan "rad etildi" yolg'on bo'ladi.

    Navbat tartibini kafolatlash o'rniga yuborishdan oldin haqiqat qayta o'qiladi.
    """
    _token, payment_id = _paid_session(client, telegram_user_id=559)
    with db_session(client) as db:
        PremiumPaymentService(db).reject_payment(payment_id, approved_by="test")

    rejected = _rows(client, kind=USER_REJECTED)
    assert rejected, "rad etish xabari navbatga tushmadi"

    with db_session(client) as db:
        PremiumPaymentService(db).approve_payment(payment_id, approved_by="test")

    bot = AsyncMock()
    run(outbox_worker.deliver_one(bot, client.testing_session_factory, rejected[0].id))

    bot.send_message.assert_not_awaited()
    with db_session(client) as db:
        assert db.get(NotificationOutbox, rejected[0].id).status == NotificationStatus.CANCELLED.value


def test_an_unknown_kind_survives_a_rollback_deploy(client):
    """Eski ishchi tushunmagan qator terminal QILINMAYDI."""
    with db_session(client) as db:
        outbox.enqueue(db, kind="kelajakdagi_tur", chat_id=1, params={}, key="kelajak-1")
        db.commit()
        row_id = db.scalar(select(NotificationOutbox.id))

    bot = AsyncMock()
    run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        assert row.status == NotificationStatus.PENDING.value
        assert (as_utc(row.next_attempt_at) - utcnow()).total_seconds() > 600
    bot.send_message.assert_not_awaited()


def test_malformed_params_of_a_known_kind_are_marked_invalid(client):
    with db_session(client) as db:
        outbox.enqueue(db, kind=USER_APPROVED, chat_id=1, params={}, key="nuqsonli-1")
        db.commit()
        row_id = db.scalar(select(NotificationOutbox.id))

    run(outbox_worker.drain_once(AsyncMock(), client.testing_session_factory, limit=10))
    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).status == NotificationStatus.INVALID.value


def test_the_worker_writes_a_heartbeat(client):
    run(outbox_worker.drain_once(AsyncMock(), client.testing_session_factory, limit=10))
    with db_session(client) as db:
        assert outbox.heartbeat_seen_at(db, OUTBOX_WORKER_HEARTBEAT) is not None


def test_a_stale_receipt_file_id_falls_back_to_plain_text(client, monkeypatch):
    """Chek rasmi yuborilmasa ham admin xabardor bo'lishi kerak — sotuv shunga bog'liq."""
    monkeypatch.setattr(settings, "admin_telegram_id", 424242)
    _token, payment_id = _paid_session(client, telegram_user_id=560)
    rows = _rows(client, kind=ADMIN_RECEIPT)
    assert rows

    bot = AsyncMock()
    bot.send_photo.side_effect = _telegram_error(TelegramBadRequest)
    run(outbox_worker.deliver_one(bot, client.testing_session_factory, rows[0].id))

    bot.send_message.assert_awaited_once()
    with db_session(client) as db:
        assert db.get(NotificationOutbox, rows[0].id).status == NotificationStatus.SENT.value
        assert f"Payment ID: {payment_id}" in bot.send_message.await_args.args[1]


# --------------------------------------------------------------------------- admin paneli


def test_the_notifications_page_flags_a_dead_worker(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_telegram_id", 424242)
    _paid_session(client, telegram_user_id=561)
    admin_login(client)
    page = client.get("/admin/notifications?filter=pending")
    assert page.status_code == 200
    assert "Ishchi javob bermayapti" in page.text


def test_the_retry_button_resets_the_attempt_budget(client):
    row_id = _enqueue_one(client)
    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        row.status = NotificationStatus.FAILED.value
        row.attempts = 8
        row.last_error = "eski xato"
        db.commit()
    admin_login(client)

    client.post(f"/admin/notifications/{row_id}/retry", data={"filter": "failed"})
    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        assert row.status == NotificationStatus.PENDING.value
        assert row.attempts == 0
        assert row.last_error is None


def test_a_persistent_flood_limit_eventually_gives_up(client):
    """Flood-limit urinishni "bepul" qiladi, lekin CHEKSIZ emas.

    Aks holda uzluksiz flood-limitdagi qator urinishlar sonini hech qachon
    tugatmasdan abadiy aylanaverardi.
    """
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        row.max_attempts = 1
        row.created_at = utcnow() - timedelta(days=2)
        db.commit()

    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramRetryAfter)
    run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        assert db.get(NotificationOutbox, row_id).status == NotificationStatus.FAILED.value


def test_a_fresh_flood_limited_row_keeps_its_budget(client):
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    with db_session(client) as db:
        db.get(NotificationOutbox, row_id).max_attempts = 1
        db.commit()

    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramRetryAfter)
    run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        assert row.status == NotificationStatus.PENDING.value
        assert row.attempts == 0


def test_an_unexpected_build_error_does_not_strand_the_batch(client, monkeypatch):
    """Xabarni qurishdagi kutilmagan xato butun paketni to'xtatib qo'yardi.

    `build_message` faqat KeyError/TypeError/ValueError ni ushlaydi; natija kontenti
    yo'q sessiya HTTPException beradi va u chiqib ketsa qator "sending" holatida
    ijara tugagunga qadar qotib turardi — qolgan qatorlar bilan birga.
    """
    session_id = _premium_session_id(client)
    poison = _enqueue_one(client, kind=PREMIUM_PDF, session_id=session_id)
    sibling = _enqueue_one(client, kind=USER_APPROVED, session_id=session_id)

    def boom(*_args, **_kwargs):
        raise RuntimeError("kutilmagan")

    monkeypatch.setattr("app.bot.messages.premium_pdf_message", boom)
    bot = AsyncMock()
    run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        poison_row = db.get(NotificationOutbox, poison)
        sibling_row = db.get(NotificationOutbox, sibling)
    # Nuqsonli qator qayta urinishga qo'yiladi, "sending" da qotib qolmaydi.
    assert poison_row.status == NotificationStatus.PENDING.value
    assert "kutilmagan" in (poison_row.last_error or "")
    # Qo'shni qator o'z yo'lida yuborilgan.
    assert sibling_row.status == NotificationStatus.SENT.value


def test_releasing_a_claim_refunds_the_attempt(client):
    """Jarayon yuborishga yetmasdan to'xsa, urinish sarflanmagan bo'ladi.

    Aks holda noto'g'ri BOT_TOKEN sababli bir necha aylanish hech qachon
    yuborilmagan xabarning butun byudjetini yeb qo'yardi.
    """
    row_id = _enqueue_one(client, kind=USER_APPROVED, session_id=_premium_session_id(client))
    bot = AsyncMock()
    bot.send_message.side_effect = _telegram_error(TelegramUnauthorizedError)

    for _ in range(3):
        with pytest.raises(outbox_worker.ProcessLevelError):
            run(outbox_worker.drain_once(bot, client.testing_session_factory, limit=10))

    with db_session(client) as db:
        row = db.get(NotificationOutbox, row_id)
        assert row.status == NotificationStatus.PENDING.value
        assert row.attempts == 0, "band qilishda oshirilgan urinish qaytarilishi kerak"


def test_a_stale_reclaim_also_refunds_the_attempt(client):
    row_id = _enqueue_one(client)
    with db_session(client) as db:
        outbox.claim_batch(db, worker_id="dead", limit=10)
        assert db.get(NotificationOutbox, row_id).attempts == 1
        db.get(NotificationOutbox, row_id).lease_expires_at = utcnow() - timedelta(minutes=5)
        db.commit()
        outbox.reclaim_stale(db)
        assert db.get(NotificationOutbox, row_id).attempts == 0


def test_a_manual_grant_then_an_approval_does_not_notify_twice(client):
    """Ikki ishlab chiqaruvchi bitta hodisani anglatadi: premium ochildi."""
    token, payment_id = _paid_session(client, telegram_user_id=571)
    admin_login(client)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id

    client.post(f"/admin/personality/{session_id}/grant-premium")
    client.post(f"/admin/premium-requests/{payment_id}/approve")

    approvals = _rows(client, kind=USER_APPROVED)
    pdfs = _rows(client, kind=PREMIUM_PDF)
    assert len(approvals) == 1, "mijoz ikkita xabar olmasligi kerak"
    assert len(pdfs) == 1, "mijoz ikkita PDF olmasligi kerak"

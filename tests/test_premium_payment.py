"""Premium toʻlov servisi: deep-link, chek, moderatsiya va natija sahifasidagi holat."""

from sqlalchemy import func, select

from app.i18n import t
from app.models.payment_request import PaymentRequest
from app.personality.payment_code import payment_code_for_session
from app.services.premium_payment_service import PremiumPaymentService, parse_premium_session_token
from tests.helpers import (
    admin_login,
    complete_session,
    db_session,
    latest_session,
    payment_code_for_token,
    session_by_token,
)

LOCKED_PREMIUM_MARKER = "mbti-premium-locked-note"


def test_parse_premium_token():
    assert parse_premium_session_token("premium_abc123") == "abc123"
    assert parse_premium_session_token("invalid") is None
    assert parse_premium_session_token("") is None
    assert parse_premium_session_token("premium_") is None
    assert parse_premium_session_token("premium_" + "a" * 65) is None
    assert parse_premium_session_token("premium_not-alnum") is None


def test_deeplink_binds_telegram_user(client):
    token = complete_session(client)
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=111222333,
            telegram_username="testuser",
            telegram_first_name="Ali",
        )
        assert outcome.code == "created"
        assert outcome.session is not None
        assert outcome.session.telegram_user_id == 111222333
        assert outcome.session.premium_requested is True
        assert outcome.payment is not None
        assert outcome.payment.session_id == outcome.session.id


def test_invalid_session_token_rejected(client):
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token="doesnotexist",
            telegram_user_id=1,
            telegram_username=None,
            telegram_first_name=None,
        )
        assert outcome.code == "invalid_token"


def test_incomplete_session_cannot_request_premium(client):
    client.get("/personality/instructions")
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=latest_session(db).token,
            telegram_user_id=99,
            telegram_username=None,
            telegram_first_name=None,
        )
        assert outcome.code == "incomplete"


def test_duplicate_deeplink_no_duplicate_payment(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        first = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=555,
            telegram_username="u1",
            telegram_first_name="A",
        )
        second = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=555,
            telegram_username="u1",
            telegram_first_name="A",
        )
        assert first.payment is not None
        assert second.payment is not None
        assert first.payment.id == second.payment.id
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1


def test_other_session_not_premium_on_approve(client):
    token_a = complete_session(client)
    client.post("/personality/restart", follow_redirects=False)
    token_b = complete_session(client)

    with db_session(client) as db:
        service = PremiumPaymentService(db)
        pay_a = service.start_premium_from_deeplink(
            session_token=token_a,
            telegram_user_id=777,
            telegram_username="same",
            telegram_first_name="User",
        ).payment
        service.start_premium_from_deeplink(
            session_token=token_b,
            telegram_user_id=777,
            telegram_username="same",
            telegram_first_name="User",
        )
        assert pay_a is not None
        service.approve_payment(pay_a.id, approved_by="test")

        assert session_by_token(db, token_a).is_premium is True
        assert session_by_token(db, token_b).is_premium is False


def test_receipt_attached_to_correct_request(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=888,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        outcome = service.attach_receipt(
            telegram_user_id=888,
            receipt_file_id="file123",
            receipt_type="photo",
            payment_id=payment.id,
        )
        assert outcome.code == "saved"
        assert outcome.payment is not None
        assert outcome.payment.receipt_file_id == "file123"
        assert outcome.payment.status == "receipt_sent"


def test_admin_approve_opens_single_session(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=999,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        mod = service.approve_payment(payment.id, approved_by="admin-test")
        assert mod.code == "approved"

        session = session_by_token(db, token)
        assert session.is_premium is True
        assert session.premium_approved_at is not None


def test_admin_reject_does_not_open_premium(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1001,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.reject_payment(payment.id, approved_by="admin-test")

        session = session_by_token(db, token)
        assert session.is_premium is False
        assert session.premium_requested is True


def test_duplicate_approve_idempotent(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1002,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.approve_payment(payment.id, approved_by="admin")
        assert service.approve_payment(payment.id, approved_by="admin").code == "already_approved"


def test_reject_is_refused_once_the_session_is_premium(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1010,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.approve_payment(payment.id, approved_by="admin")
        assert service.reject_payment(payment.id, approved_by="admin").code == "already_approved"


def test_payment_status_transitions_shown_on_the_result_page(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        session = session_by_token(db, token)
        assert service.get_result_payment_status(session) == "unpaid"

    assert client.post(f"/personality/result/{token}/support-bot", follow_redirects=False).status_code == 303
    awaiting = client.get(f"/personality/result/{token}")
    assert "mbti-premium-status--pending" in awaiting.text
    assert t("result.status_awaiting_title", "uz") in awaiting.text

    code = payment_code_for_token(client, token)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        claimed = service.claim_by_payment_code(
            payment_code=code,
            telegram_user_id=2020,
            telegram_username=None,
            telegram_first_name=None,
        )
        assert claimed.code == "claimed"
        saved = service.attach_receipt(
            telegram_user_id=2020,
            receipt_file_id="file-1",
            receipt_type="photo",
        )
        assert saved.code == "saved"
        # Vebda egasiz boshlangan qator yangisi bilan almashmaydi.
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 1

    reviewing = client.get(f"/personality/result/{token}")
    assert t("result.status_pending_title", "uz") in reviewing.text


def test_non_premium_session_hides_premium_content(client):
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert LOCKED_PREMIUM_MARKER in page.text
    assert page.text.count("mbti-premium-card is-locked") == 6
    assert "mbti-premium-success-badge" not in page.text


def test_premium_session_shows_premium_content(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1003,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.approve_payment(payment.id, approved_by="test")

    page = client.get(f"/personality/result/{token}")
    assert LOCKED_PREMIUM_MARKER not in page.text
    assert "is-locked" not in page.text
    assert t("result.premium_opened", "uz") in page.text
    assert t("result.premium.brief", "uz") in page.text


def test_cannot_view_other_session_result(client):
    token_a = complete_session(client)
    client.cookies.clear()
    token_b = complete_session(client)
    assert token_a != token_b

    denied = client.get(f"/personality/result/{token_a}", follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers["location"] == "/personality"


def test_admin_search_by_payment_code(client):
    token = complete_session(client)
    code = payment_code_for_token(client, token)

    admin_login(client)
    found = client.get(f"/admin/sessions?code={code}")
    assert found.status_code == 200
    assert token[:8] in found.text or code in found.text


def test_payment_code_is_stable_across_lookups(client):
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert payment_code_for_session(db, session) == payment_code_for_session(db, session)
        assert token.startswith(session.payment_code)


def test_manual_grant_without_payment_request(client):
    token = complete_session(client)
    admin_login(client)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        assert db.scalar(select(func.count()).select_from(PaymentRequest)) == 0

    response = client.post(f"/admin/sessions/{session_id}/grant-premium", follow_redirects=False)
    assert response.status_code == 303
    assert "flash=premium_ok" in response.headers["location"]

    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.is_premium is True
        assert session.premium_approved_at is not None

    page = client.get(f"/personality/result/{token}")
    assert LOCKED_PREMIUM_MARKER not in page.text


def test_manual_grant_is_idempotent(client):
    token = complete_session(client)
    admin_login(client)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id

    client.post(f"/admin/sessions/{session_id}/grant-premium")
    again = client.post(f"/admin/sessions/{session_id}/grant-premium", follow_redirects=False)
    assert again.status_code == 303
    assert "flash=premium_ok" not in (again.headers.get("location") or "")


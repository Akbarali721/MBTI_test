import re

from sqlalchemy import func, select

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityTestSession
from app.services.premium_payment_service import PremiumPaymentService, parse_premium_session_token


def _complete_session(client, theme: str = "male") -> str:
    client.get("/personality/instructions")
    post = client.post("/personality/start", data={"gender": theme}, follow_redirects=False)
    assert post.status_code == 303
    token = post.headers["location"].rstrip("/").split("/")[-1]
    for question_index in range(24):
        page = client.get(f"/personality/test/{token}?q={question_index}")
        assert page.status_code == 200
        qid = int(re.search(r'name="question_id" value="(\d+)"', page.text).group(1))
        oid = int(re.search(r'name="option_id"\s+value="(\d+)"', page.text).group(1))
        client.post(
            f"/personality/test/{token}/answer",
            data={"question_id": qid, "option_id": oid, "question_index": str(question_index)},
            follow_redirects=False,
        )
    client.get(f"/personality/result/{token}/loading")
    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200
    return token


def test_parse_premium_token():
    assert parse_premium_session_token("premium_abc123") == "abc123"
    assert parse_premium_session_token("invalid") is None


def test_deeplink_binds_telegram_user(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        service = PremiumPaymentService(db)
        outcome = service.start_premium_from_deeplink(
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
    finally:
        db.close()


def test_invalid_session_token_rejected(client):
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token="doesnotexist",
            telegram_user_id=1,
            telegram_username=None,
            telegram_first_name=None,
        )
        assert outcome.code == "invalid_token"
    finally:
        db.close()


def test_incomplete_session_cannot_request_premium(client):
    client.get("/personality/instructions")
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        row = db.scalar(select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1))
        assert row is not None
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=row.token,
            telegram_user_id=99,
            telegram_username=None,
            telegram_first_name=None,
        )
        assert outcome.code == "incomplete"
    finally:
        db.close()


def test_duplicate_deeplink_no_duplicate_payment(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
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
        count = db.scalar(select(func.count()).select_from(PaymentRequest))
        assert count == 1
    finally:
        db.close()


def test_other_session_not_premium_on_approve(client):
    token_a = _complete_session(client)
    client.post("/personality/restart", follow_redirects=False)
    token_b = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
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
        sess_a = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token_a))
        sess_b = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token_b))
        assert sess_a is not None and sess_b is not None
        assert sess_a.is_premium is True
        assert sess_b.is_premium is False
    finally:
        db.close()


def test_receipt_attached_to_correct_request(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
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
    finally:
        db.close()


def test_admin_approve_opens_single_session(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
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
        sess = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert sess is not None
        assert sess.is_premium is True
        assert sess.premium_approved_at is not None
    finally:
        db.close()


def test_admin_reject_does_not_open_premium(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1001,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.reject_payment(payment.id, approved_by="admin-test")
        sess = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert sess is not None
        assert sess.is_premium is False
        assert sess.premium_requested is True
    finally:
        db.close()


def test_duplicate_approve_idempotent(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1002,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        service.approve_payment(payment.id, approved_by="admin")
        again = service.approve_payment(payment.id, approved_by="admin")
        assert again.code == "already_approved"
    finally:
        db.close()


def test_non_premium_session_hides_premium_content(client):
    token = _complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert "Premium tahlil — ochish uchun to‘lov tasdiqlanishi kerak" in page.text
    assert "maqsad aniq va natija ko‘rinadigan bo‘lganda oshadi" not in page.text


def test_premium_session_shows_premium_content(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        payment = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=1003,
            telegram_username=None,
            telegram_first_name=None,
        ).payment
        assert payment is not None
        PremiumPaymentService(db).approve_payment(payment.id, approved_by="test")
    finally:
        db.close()
    page = client.get(f"/personality/result/{token}")
    assert "Premium tahlil — ochish uchun" not in page.text
    assert "Motivatsiyangiz" in page.text or "motivatsiyangiz" in page.text.lower()


def test_cannot_view_other_session_result(client):
    token_a = _complete_session(client)
    client.cookies.clear()
    token_b = _complete_session(client)
    assert token_a != token_b
    denied = client.get(f"/personality/result/{token_a}", follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers["location"] == "/personality"



def test_admin_search_by_payment_code(client):
    from app.config import settings

    token = _complete_session(client)
    from app.personality.payment_code import payment_code_for_session

    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        from sqlalchemy import select

        from app.models.personality import PersonalityTestSession

        row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert row is not None
        code = payment_code_for_session(db, row)
    finally:
        db.close()

    client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    found = client.get(f"/admin/sessions?code={code}")
    assert found.status_code == 200
    assert token[:8] in found.text or code in found.text


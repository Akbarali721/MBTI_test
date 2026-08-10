"""Premium tasdiqlash Telegram yetkazilishi premiumni buzmasligi kerak."""

from unittest.mock import patch

from app.services.premium_payment_service import PremiumPaymentService
from tests.helpers import admin_login, complete_session, db_session, session_by_token


def test_admin_approve_keeps_premium_when_telegram_delivery_fails(client):
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        payment = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=4242,
            telegram_username="payer",
            telegram_first_name="Payer",
        ).payment
        assert payment is not None
        payment_id = payment.id

    admin_login(client)
    with patch(
        "app.routers.admin.try_deliver_premium_approved_message",
        return_value="Telegram xabari yuborilmadi.",
    ):
        response = client.post(
            f"/admin/premium-requests/{payment_id}/approve",
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert "premium_telegram_failed" in response.headers["location"]

    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is True

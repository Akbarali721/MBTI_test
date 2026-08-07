"""Admin paneldagi toʻlov moderatsiyasi va chek proksisi.

Chek Telegramʼdan proksi qilinadi: bot tokeni hech qachon brauzerga chiqmasligi kerak.
"""

import json

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.payment_request import PaymentRequest
from app.routers import admin
from app.services.premium_payment_service import PremiumPaymentService
from tests.helpers import admin_login, complete_session, db_session, session_by_token

BOT_TOKEN = "123456:test-token"


class _FakeGetFileResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, *_args) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False


class _FakeDownloadResponse:
    def __init__(self, data: bytes, content_type: str | None) -> None:
        self._chunks = [data]
        self.headers = {"Content-Type": content_type} if content_type else {}

    def read(self, *_args) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False


def _fake_telegram(monkeypatch, *, file_path="photos/file_1.jpg", data=b"CHEK", content_type="image/jpeg"):
    calls: list[str] = []

    def _open(url, *_args, **_kwargs):
        calls.append(url)
        if "/getFile" in url:
            return _FakeGetFileResponse(json.dumps({"ok": True, "result": {"file_path": file_path}}).encode())
        return _FakeDownloadResponse(data, content_type)

    monkeypatch.setattr(admin, "urlopen", _open)
    return calls


@pytest.fixture()
def payment(client):
    """Chek yuborilgan, moderatsiyani kutayotgan toʻlov."""
    token = complete_session(client)
    with db_session(client) as db:
        service = PremiumPaymentService(db)
        created = service.start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=31337,
            telegram_username="payer",
            telegram_first_name="Ali",
        ).payment
        assert created is not None
        service.attach_receipt(
            telegram_user_id=31337,
            receipt_file_id="receipt-file-id",
            receipt_type="photo",
            payment_id=created.id,
        )
        payment_id = created.id
    return token, payment_id


def test_admin_can_approve_a_payment_from_the_panel(client, payment):
    token, payment_id = payment
    admin_login(client)

    response = client.post(f"/admin/premium-requests/{payment_id}/approve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/premium-requests"

    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is True
        assert db.get(PaymentRequest, payment_id).approved_by == "web-admin"


def test_admin_can_reject_a_payment_from_the_panel(client, payment):
    token, payment_id = payment
    admin_login(client)

    response = client.post(f"/admin/premium-requests/{payment_id}/reject", follow_redirects=False)
    assert response.status_code == 303

    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is False
        assert db.get(PaymentRequest, payment_id).status == "rejected"


def test_premium_requests_list_shows_the_pending_receipt(client, payment):
    _, payment_id = payment
    admin_login(client)

    page = client.get("/admin/premium-requests")
    assert page.status_code == 200
    assert str(payment_id) in page.text


def test_receipt_is_proxied_without_leaking_the_bot_token(client, payment, monkeypatch):
    _, payment_id = payment
    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)
    calls = _fake_telegram(monkeypatch)
    admin_login(client)

    response = client.get(f"/admin/premium-requests/{payment_id}/receipt")

    assert response.status_code == 200
    assert response.content == b"CHEK"
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.headers["cache-control"] == "private, no-store"
    assert BOT_TOKEN not in response.text
    assert any("/getFile" in url for url in calls)


def test_receipt_falls_back_to_a_guessed_media_type(client, payment, monkeypatch):
    _, payment_id = payment
    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)
    _fake_telegram(monkeypatch, file_path="documents/chek.pdf", content_type=None)
    admin_login(client)

    response = client.get(f"/admin/premium-requests/{payment_id}/receipt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")


def test_receipt_404_when_the_payment_has_none(client, monkeypatch):
    token = complete_session(client)
    with db_session(client) as db:
        created = (
            PremiumPaymentService(db)
            .start_premium_from_deeplink(
                session_token=token,
                telegram_user_id=42,
                telegram_username=None,
                telegram_first_name=None,
            )
            .payment
        )
        assert created is not None
        payment_id = created.id

    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)
    admin_login(client)

    response = client.get(f"/admin/premium-requests/{payment_id}/receipt")
    assert response.status_code == 404
    assert "chek yo‘q" in response.json()["detail"]


def test_receipt_404_when_telegram_refuses_the_file(client, payment, monkeypatch):
    _, payment_id = payment
    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)
    monkeypatch.setattr(
        admin,
        "urlopen",
        lambda *_a, **_k: _FakeGetFileResponse(json.dumps({"ok": False}).encode()),
    )
    admin_login(client)

    response = client.get(f"/admin/premium-requests/{payment_id}/receipt")
    assert response.status_code == 404


def test_receipt_404_when_the_download_connection_fails(client, payment, monkeypatch):
    _, payment_id = payment
    monkeypatch.setattr(settings, "bot_token", BOT_TOKEN)

    def _open(url, *_args, **_kwargs):
        if "/getFile" in url:
            return _FakeGetFileResponse(
                json.dumps({"ok": True, "result": {"file_path": "photos/f.jpg"}}).encode()
            )
        raise OSError("tarmoq yopiq")

    monkeypatch.setattr(admin, "urlopen", _open)
    admin_login(client)

    response = client.get(f"/admin/premium-requests/{payment_id}/receipt")
    assert response.status_code == 404


def test_moderation_routes_require_login(client, payment):
    _, payment_id = payment
    for method, path in (
        ("POST", f"/admin/premium-requests/{payment_id}/approve"),
        ("POST", f"/admin/premium-requests/{payment_id}/reject"),
        ("GET", f"/admin/premium-requests/{payment_id}/receipt"),
    ):
        response = client.request(method, path, follow_redirects=False)
        assert response.status_code == 303, (method, path)
        assert response.headers["location"] == "/admin/login"

    with db_session(client) as db:
        assert db.scalar(select(PaymentRequest)).status == "receipt_sent"

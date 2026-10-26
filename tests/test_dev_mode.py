"""DEV_MODE va TELEGRAM_WEBAPP_ONLY himoyasi."""

import pytest

from app.config import settings
from app.i18n import t
from app.personality.analytics_constants import DEV_BROWSER_SOURCE
from tests.helpers import complete_session, db_session, session_by_token, start_session


def _patch_local_webapp_gate(monkeypatch, *, dev_mode: bool) -> None:
    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "public_base_url", "http://127.0.0.1:8000", raising=False)
    monkeypatch.setattr(settings, "dev_mode", dev_mode, raising=False)
    monkeypatch.setattr(settings, "telegram_webapp_only", True, raising=False)


def test_dev_mode_active_only_on_local_debug():
    from app.config import Settings

    assert (
        Settings(
            debug=True,
            secret_key="test-secret-key-not-a-placeholder",
            admin_password_hash="x",
            public_base_url="http://127.0.0.1:8000",
            dev_mode=True,
        ).dev_mode_active
        is True
    )
    assert (
        Settings(
            debug=True,
            secret_key="test-secret-key-not-a-placeholder",
            admin_password_hash="x",
            public_base_url="https://prod.example",
            dev_mode=True,
        ).dev_mode_active
        is False
    )


def test_dev_mode_refused_in_production():
    from app.config import Settings

    with pytest.raises(RuntimeError, match="DEV_MODE"):
        Settings(
            debug=False,
            secret_key="kuchli-kalit-" + "x" * 32,
            admin_password_hash="$2b$04$x",
            admin_username="operator",
            public_base_url="https://prod.example",
            dev_mode=True,
        )


def test_dev_mode_refused_on_railway(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Railway"):
        Settings(
            debug=True,
            secret_key="test-secret-key-not-a-placeholder",
            admin_password_hash="x",
            public_base_url="http://127.0.0.1:8000",
            dev_mode=True,
        )


def test_webapp_only_blocks_test_without_telegram(client, monkeypatch):
    _patch_local_webapp_gate(monkeypatch, dev_mode=False)
    token = start_session(client, "male")
    page = client.get(f"/personality/test/{token}?q=0")
    assert page.status_code == 404
    assert t("errors.message_webapp_only", "uz") in page.text


def test_dev_mode_bypasses_gate_on_local_host_with_prod_public_url(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "public_base_url", "https://prod.example", raising=False)
    monkeypatch.setattr(settings, "dev_mode", True, raising=False)
    monkeypatch.setattr(settings, "telegram_webapp_only", True, raising=False)
    assert settings.dev_mode_active is False
    token = complete_session(client)
    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200


def test_dev_mode_allows_full_flow(client, monkeypatch):
    _patch_local_webapp_gate(monkeypatch, dev_mode=True)
    token = complete_session(client)
    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200
    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.source == DEV_BROWSER_SOURCE
        assert row.telegram_user_id == settings.dev_browser_telegram_id


def test_completed_session_via_instructions_not_webapp_404(client, monkeypatch):
    """Eski cookie (dev-browser yo‘q) + TELEGRAM_WEBAPP_ONLY: instructions → natija 404 bo‘lmasin."""
    monkeypatch.setattr(settings, "dev_mode", False, raising=False)
    monkeypatch.setattr(settings, "telegram_webapp_only", False, raising=False)
    complete_session(client)
    _patch_local_webapp_gate(monkeypatch, dev_mode=True)
    page = client.get("/personality/instructions", follow_redirects=True)
    assert page.status_code == 200
    assert t("errors.message_webapp_only", "uz") not in page.text


def test_root_redirects_to_instructions_when_dev_mode_active(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "public_base_url", "http://127.0.0.1:8000", raising=False)
    monkeypatch.setattr(settings, "dev_mode", True, raising=False)
    assert settings.dev_mode_active is True
    root = client.get("/", follow_redirects=False)
    assert root.status_code == 303
    assert root.headers["location"] == "/personality/instructions"

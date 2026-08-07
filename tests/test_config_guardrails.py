"""Sozlama himoyasi: DEBUG=false da xavfsiz boʻlmagan qiymat ishga tushirmasligi kerak."""

import pytest

from app.config import PLACEHOLDER_SECRET_KEYS, Settings

# Ishlab chiqarish uchun yaroqli minimal toʻplam; har test undan bitta qiymatni buzadi.
PRODUCTION_SETTINGS = {
    "debug": False,
    "secret_key": "kuchli-tasodifiy-kalit-" + "x" * 32,
    "admin_username": "operator",
    "admin_password": "",
    "admin_password_hash": "$2b$04$C4rDzMJb5V1o8Bq2xkxYbeH8tD5b1H0kK1s8h0S4rQ0nq0bH0m2Iu",
    "public_base_url": "https://xarakter.example",
    # Aniq beriladi: ishlab chiquvchining .env fayli testga ta'sir qilmasin.
    "secure_cookies": None,
}


def _settings(**overrides) -> Settings:
    return Settings(**{**PRODUCTION_SETTINGS, **overrides})


def test_valid_production_settings_are_accepted():
    settings = _settings()
    assert settings.debug is False
    assert settings.secret_key_is_weak is False
    assert settings.secure_cookies_enabled is True


@pytest.mark.parametrize("placeholder", [*sorted(PLACEHOLDER_SECRET_KEYS), "", "   "])
def test_placeholder_secret_key_is_refused_in_production(placeholder):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _settings(secret_key=placeholder)


def test_admin_admin_password_is_refused_in_production():
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD sifatida"):
        _settings(admin_password="admin")


def test_admin_username_admin_is_refused_in_production():
    with pytest.raises(RuntimeError, match="ADMIN_USERNAME"):
        _settings(admin_username="admin")


def test_missing_password_hash_is_refused_in_production():
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD_HASH"):
        _settings(admin_password_hash="", admin_password="yetarlicha-uzun-parol")


def test_no_credentials_at_all_is_refused_in_production():
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD_HASH"):
        _settings(admin_password_hash="", admin_password="")


def test_local_public_base_url_is_refused_in_production():
    with pytest.raises(RuntimeError, match="PUBLIC_BASE_URL"):
        _settings(public_base_url="http://127.0.0.1:8000")


def test_debug_mode_only_warns_and_generates_a_session_key(caplog):
    with caplog.at_level("WARNING"):
        settings = _settings(debug=True, secret_key="dev-secret-key", admin_username="admin")

    assert settings.secret_key not in PLACEHOLDER_SECRET_KEYS
    assert len(settings.secret_key) >= 32
    assert any("SECRET_KEY" in record.getMessage() for record in caplog.records)


def test_debug_mode_hashes_a_plaintext_admin_password():
    settings = _settings(debug=True, admin_password_hash="", admin_password="lokal-parol")
    assert settings.admin_password_hash.startswith("$2")


def test_blank_optional_values_fall_back_to_defaults():
    settings = _settings(content_security_policy="", log_level="  ", secure_cookies="")
    assert "frame-ancestors 'none'" in settings.content_security_policy
    assert settings.log_level == "INFO"
    # secure_cookies avtomatik: DEBUG=false da yoqiladi.
    assert settings.secure_cookies is None
    assert settings.secure_cookies_enabled is True

"""Telegram WebApp initData tekshiruvi."""

import hashlib
import hmac
import json
from urllib.parse import urlencode

from app.telegram.webapp_auth import parse_webapp_user, validate_init_data

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


def _signed_init_data(user: dict, *, auth_date: str = "1700000000") -> str:
    payload = {
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": auth_date,
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload["hash"] = digest
    return urlencode(payload)


def test_validate_init_data_accepts_valid_signature():
    raw = _signed_init_data({"id": 42, "username": "ali", "first_name": "Ali"})
    assert validate_init_data(raw, BOT_TOKEN) is not None


def test_validate_init_data_rejects_tampered_payload():
    raw = _signed_init_data({"id": 42})
    tampered = raw.replace("42", "99")
    assert validate_init_data(tampered, BOT_TOKEN) is None


def test_parse_webapp_user_returns_structured_user():
    raw = _signed_init_data({"id": 77, "username": "tester", "first_name": "Test"})
    user = parse_webapp_user(raw, BOT_TOKEN)
    assert user is not None
    assert user.id == 77
    assert user.username == "tester"
    assert user.first_name == "Test"

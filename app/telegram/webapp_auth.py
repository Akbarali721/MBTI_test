"""Telegram Mini App initData tekshiruvi (server-side).

Frontenddan kelgan `telegram_user_id` ishonilmaydi — faqat bot token bilan
HMAC-SHA256 orqali tasdiqlangan initData qabul qilinadi.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class TelegramWebAppUser:
    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


def validate_init_data(init_data: str, bot_token: str) -> dict[str, str] | None:
    """Telegram WebApp initData ni tekshiradi. Yaroqsiz bo'lsa None."""
    token = (bot_token or "").strip()
    raw = (init_data or "").strip()
    if not token or not raw:
        return None

    parsed = dict(parse_qsl(raw, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        return None
    return parsed


def parse_webapp_user(init_data: str, bot_token: str) -> TelegramWebAppUser | None:
    fields = validate_init_data(init_data, bot_token)
    if fields is None:
        return None
    user_json = fields.get("user")
    if not user_json:
        return None
    try:
        payload = json.loads(user_json)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    user_id = payload.get("id")
    if not isinstance(user_id, int):
        return None
    username = payload.get("username")
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    return TelegramWebAppUser(
        id=user_id,
        username=username if isinstance(username, str) and username else None,
        first_name=first_name if isinstance(first_name, str) and first_name else None,
        last_name=last_name if isinstance(last_name, str) and last_name else None,
    )

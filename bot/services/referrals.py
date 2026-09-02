"""Bot handlerlari uchun referal xizmati."""

from __future__ import annotations

from app.services.telegram_referral_service import (
    attribute_bot_referral,
    parse_referral_telegram_id,
    telegram_referral_url,
)

__all__ = [
    "attribute_bot_referral",
    "parse_referral_telegram_id",
    "telegram_referral_url",
]

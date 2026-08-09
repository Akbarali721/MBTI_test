"""Vaqt bilan ishlashning umumiy qoidalari.

Ikkita nozik joy bor va ular butun loyihada bir xil hal qilinadi:

* SQLite `DateTime(timezone=True)` da ofsetni saqlamaydi — o'qishda qiymat "naive"
  bo'lib qaytadi, Postgres esa "aware" beradi. Ularni solishtirish `TypeError` bilan
  tugaydi, shuning uchun o'qilgan har qiymat `as_utc()` dan o'tkaziladi.
* O'zbekistonda yozgi vaqt yo'q, ya'ni UTC+5 qat'iy. Shu sabab tzdata kerak emas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

TASHKENT_TZ = timezone(timedelta(hours=5))


def as_utc(value: datetime | None) -> datetime | None:
    """Naive qiymatni UTC deb belgilaydi, aware qiymatni UTC ga keltiradi."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def tashkent_day_start(now: datetime | None = None) -> datetime:
    """Asia/Tashkent bo'yicha bugungi kun boshini UTC lahzasi sifatida qaytaradi.

    Bazadagi vaqtlar UTC'da saqlanadi, "bugun" esa admin uchun mahalliy kun bo'lishi kerak.
    """
    moment = as_utc(now) or utcnow()
    local_midnight = moment.astimezone(TASHKENT_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(timezone.utc)


def format_tashkent(value: datetime | None) -> str:
    """Eksport va hisobotlar uchun mahalliy vaqt (ofsetsiz — Excel uni matn deb o'qiydi)."""
    moment = as_utc(value)
    if moment is None:
        return ""
    return moment.astimezone(TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")

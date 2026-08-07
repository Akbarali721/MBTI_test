"""Sessiyalar va to'lovlarni CSV ga chiqarish.

Uchta qaror ataylab qilingan:

* **Ustunlar ro'yxati yopiq.** `token`, `payment_code` va `share_code` hech qachon
  chiqmaydi. To'lov kodi — bu tokenning boshlang'ich qismi, uni botga yuborgan
  ODAM sessiyani o'ziga biriktirib oladi. Ya'ni buxgalterga yuborilgan jadval
  begona natijalarni ochish vositasiga aylanardi.
* **Fayl buferlanadi, oqim emas.** Hajm cheklangan (`EXPORT_MAX_ROWS`), shuning
  uchun oqimning murakkabligi (yarim yozilgan faylga 200 javob, uzoq ochiq
  tranzaksiya) keraksiz xavf bo'lardi.
* **Matn kataklari formuladan himoyalanadi.** `source` ni autentifikatsiyasiz
  har qanday odam `?source=` orqali yozib ketishi mumkin.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import PAYMENT_STATUS_VALUES, PersonalitySessionStatus
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityTestSession
from app.timeutils import TASHKENT_TZ, format_tashkent, tashkent_day_start

# Excel (uz-UZ / ru-RU) ro'yxat ajratgichi — vergul emas, nuqtali vergul.
DELIMITER = ";"
BOM = "﻿"
LINE_TERMINATOR = "\r\n"
FORMULA_PREFIXES = ("=", "+", "-", "@")
CONTROL_TO_SPACE = {ord("\r"): " ", ord("\n"): " ", ord("\t"): " "}


class ExportTooLarge(Exception):
    def __init__(self, total: int, limit: int) -> None:
        super().__init__(f"{total} qator, chegara {limit}")
        self.total = total
        self.limit = limit


class ExportFilterError(Exception):
    pass


@dataclass(frozen=True)
class ExportFilters:
    status: str = "all"
    date_from: datetime | None = None
    date_to: datetime | None = None

    def describe(self) -> str:
        """Audit yozuvi uchun: admin AYNAN nima so'raganini ko'rsatadi.

        UTC lahzasini `.date()` bilan chiqarish bir kun oldingi sanani berardi
        (Toshkent yarim tuni = UTC 19:00), `date_to` esa ochiq yuqori chegara —
        ikkalasi ham hisobotni yolg'on ko'rsatardi.
        """
        parts = [f"filter={self.status}"]
        if self.date_from:
            parts.append(f"from={self.date_from.astimezone(TASHKENT_TZ).date()}")
        if self.date_to:
            inclusive = self.date_to - timedelta(days=1)
            parts.append(f"to={inclusive.astimezone(TASHKENT_TZ).date()}")
        return " ".join(parts)


@dataclass(frozen=True)
class CsvFile:
    filename: str
    content: bytes
    rows: int


# --- Formatlash ---


def text_cell(value: object) -> str:
    """Matn katagi: boshqaruv belgilarisiz va formulaga aylanmaydigan.

    Qo'shtirnoq yetarli emas — Excel import paytida qo'shtirnoqni olib tashlaydi va
    `=cmd|'/C calc'!A0` ni baribir bajaradi. Tekshiruv bo'sh joy olib tashlangan
    birinchi belgi bo'yicha, prefiks esa ASL satrga qo'yiladi.
    """
    if value is None:
        return ""
    text = str(value).translate(CONTROL_TO_SPACE)
    text = "".join(char for char in text if char >= " " and char != "\x7f")
    if text.lstrip()[:1] in FORMULA_PREFIXES:
        return "'" + text
    return text


def int_cell(value: object) -> str:
    """Son katagi — HECH QACHON qochirilmaydi, aks holda manfiy son matnga aylanardi."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(int(value))
    return ""


def bool_cell(value: object) -> str:
    # 1/0: Excel'dagi TRUE/FALSE tilga bog'liq, "ha/yo'q" esa yig'ilmaydi.
    return "1" if value else "0"


def date_cell(value: datetime | None) -> str:
    return format_tashkent(value)


def build_csv(header: Sequence[str], rows: Iterable[Sequence[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=DELIMITER, quoting=csv.QUOTE_ALL, lineterminator=LINE_TERMINATOR)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    # BOM aynan bir marta, eng boshida: usiz Excel faylni ANSI deb o'qiydi va
    # o'zbekcha/kirilcha harflar buziladi.
    return (BOM + buffer.getvalue()).encode("utf-8")


# --- Filtrlar ---


def parse_day(value: str | None, *, end: bool = False) -> datetime | None:
    if not value or not value.strip():
        return None
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d")
        # Toshkent kuni deb o'qiladi; oraliq [boshi, oxiri) yarim ochiq bo'ladi,
        # aks holda oxirgi kun 5 soatga kalta bo'lib qolardi.
        day_start = datetime(parsed.year, parsed.month, parsed.day, tzinfo=TASHKENT_TZ).astimezone(
            timezone.utc
        )
    except (ValueError, OverflowError):
        # OverflowError: 0001-01-01 kabi sana UTC ga o'tkazilganda datetime.min dan
        # chiqib ketadi. U ValueError emas, ya'ni ushlanmasa 500 bo'lardi.
        raise ExportFilterError("Sana YYYY-MM-DD ko'rinishida bo'lishi kerak") from None
    return day_start + timedelta(days=1) if end else day_start


def session_filters(status: str | None, date_from: str | None, date_to: str | None) -> ExportFilters:
    cleaned = (status or "all").strip() or "all"
    allowed = {"all", "today"} | {member.value for member in PersonalitySessionStatus}
    if cleaned not in allowed:
        # Jim qolib butun jadvalni chiqarish eng yomon variant: audit yozuvi tor
        # filtrni ko'rsatib turgan bo'lardi, fayl esa hamma narsani.
        raise ExportFilterError(f"Noma'lum filtr: {cleaned}")
    return ExportFilters(status=cleaned, date_from=parse_day(date_from), date_to=parse_day(date_to, end=True))


def payment_filters(status: str | None, date_from: str | None, date_to: str | None) -> ExportFilters:
    cleaned = (status or "all").strip() or "all"
    if cleaned != "all" and cleaned not in PAYMENT_STATUS_VALUES:
        raise ExportFilterError(f"Noma'lum filtr: {cleaned}")
    return ExportFilters(status=cleaned, date_from=parse_day(date_from), date_to=parse_day(date_to, end=True))


def _apply_window(stmt: Select, column: Any, filters: ExportFilters) -> Select:
    if filters.date_from is not None:
        stmt = stmt.where(column >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(column < filters.date_to)
    return stmt


# --- Sessiyalar ---

SESSION_HEADER = (
    "id",
    "holat",
    "toplam",
    "manba",
    "natija",
    "premium",
    "premium_sorovi",
    "javoblar",
    "jami_savol",
    "telegram_username",
    "telegram_ism",
    "yaratilgan (UTC+5)",
    "boshlangan (UTC+5)",
    "tugatilgan (UTC+5)",
    "oxirgi_faollik (UTC+5)",
    "premium_ochilgan (UTC+5)",
    "anonimlashtirilgan (UTC+5)",
)


def _session_query(filters: ExportFilters) -> Select:
    model = PersonalityTestSession
    stmt = select(
        model.id,
        model.status,
        model.variant,
        model.source,
        model.result_type,
        model.is_premium,
        model.premium_requested,
        model.answered_questions,
        model.total_questions,
        model.telegram_username,
        model.telegram_first_name,
        model.created_at,
        model.started_at,
        model.completed_at,
        model.last_activity_at,
        model.premium_approved_at,
        model.anonymized_at,
    ).order_by(model.id)
    if filters.status == "today":
        stmt = stmt.where(model.created_at >= tashkent_day_start())
    elif filters.status != "all":
        stmt = stmt.where(model.status == PersonalitySessionStatus(filters.status))
    return _apply_window(stmt, model.created_at, filters)


def _session_row(row: Any) -> list[str]:
    status = row[1]
    return [
        int_cell(row[0]),
        text_cell(getattr(status, "value", status)),
        text_cell(row[2]),
        text_cell(row[3]),
        text_cell(row[4]),
        bool_cell(row[5]),
        bool_cell(row[6]),
        int_cell(row[7]),
        int_cell(row[8]),
        text_cell(row[9]),
        text_cell(row[10]),
        date_cell(row[11]),
        date_cell(row[12]),
        date_cell(row[13]),
        date_cell(row[14]),
        date_cell(row[15]),
        date_cell(row[16]),
    ]


# --- To'lovlar ---

PAYMENT_HEADER = (
    "id",
    "session_id",
    "holat",
    "summa",
    "mbti",
    "telegram_id",
    "telegram_username",
    "telegram_ism",
    "chek_bor",
    "chek_turi",
    "kim_hal_qildi",
    "yaratilgan (UTC+5)",
    "chek_yuborilgan (UTC+5)",
    "tasdiqlangan (UTC+5)",
    "rad_etilgan (UTC+5)",
)


def _payment_query(filters: ExportFilters) -> Select:
    model = PaymentRequest
    session = PersonalityTestSession
    stmt = (
        select(
            model.id,
            model.session_id,
            model.status,
            model.amount,
            session.result_type,
            model.telegram_user_id,
            model.telegram_username,
            model.telegram_first_name,
            model.receipt_file_id,
            model.receipt_type,
            model.approved_by,
            model.created_at,
            model.receipt_sent_at,
            model.approved_at,
            model.rejected_at,
        )
        .join(session, session.id == model.session_id)
        .order_by(model.id)
    )
    if filters.status != "all":
        stmt = stmt.where(model.status == filters.status)
    return _apply_window(stmt, model.created_at, filters)


def _payment_row(row: Any) -> list[str]:
    return [
        int_cell(row[0]),
        int_cell(row[1]),
        text_cell(row[2]),
        # Summa toza butun son: "9 990" ko'rinishi Excel'da matn bo'lib, yig'ilmaydi.
        int_cell(row[3]),
        text_cell(row[4]),
        int_cell(row[5]),
        text_cell(row[6]),
        text_cell(row[7]),
        # file_id ning o'zi chiqarilmaydi: bot tokeni bilan u chek rasmini
        # (karta raqami ko'rinadigan) yuklab olish imkonini beradi.
        bool_cell(row[8]),
        text_cell(row[9]),
        text_cell(row[10]),
        date_cell(row[11]),
        date_cell(row[12]),
        date_cell(row[13]),
        date_cell(row[14]),
    ]


# --- Umumiy ---


def _count(db: Session, stmt: Select) -> int:
    return int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)


def _export(db: Session, stmt: Select, header: Sequence[str], mapper: Any, prefix: str) -> CsvFile:
    total = _count(db, stmt)
    if total > settings.export_max_rows:
        raise ExportTooLarge(total, settings.export_max_rows)
    rows = [mapper(row) for row in db.execute(stmt).all()]
    # Fayl nomi faqat ASCII: Starlette sarlavhalarni latin-1 da kodlaydi va
    # o'zbekcha tipografik apostrof 500 xatoga olib kelardi.
    stamp = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
    return CsvFile(filename=f"{prefix}-{stamp}.csv", content=build_csv(header, rows), rows=len(rows))


def export_sessions(db: Session, filters: ExportFilters) -> CsvFile:
    return _export(db, _session_query(filters), SESSION_HEADER, _session_row, "sessiyalar")


def export_payments(db: Session, filters: ExportFilters) -> CsvFile:
    return _export(db, _payment_query(filters), PAYMENT_HEADER, _payment_row, "tolovlar")

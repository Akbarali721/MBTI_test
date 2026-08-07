"""CSV eksport: nima chiqadi, nima CHIQMAYDI va Excel uni qanday o'qiydi."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import settings
from app.models.payment_request import PaymentRequest
from app.services import csv_export
from app.services.premium_payment_service import PremiumPaymentService
from tests.helpers import admin_login, complete_session, db_session, session_by_token

HOSTILE_SOURCE = "=cmd|'/C calc'!A0"


def _rows(body: bytes) -> list[list[str]]:
    text = body.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text), delimiter=";"))


def _cells(body: bytes) -> list[str]:
    return [cell for row in _rows(body) for cell in row]


def test_sessions_export_is_excel_ready(client):
    complete_session(client)
    admin_login(client)

    response = client.get("/admin/export/sessions.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="sessiyalar-' in response.headers["content-disposition"]
    assert "no-store" in response.headers["cache-control"]

    body = response.content
    # BOM aynan bitta va eng boshida: usiz Excel faylni ANSI deb o'qiydi.
    assert body.startswith(b"\xef\xbb\xbf")
    assert body.count(b"\xef\xbb\xbf") == 1
    header = _rows(body)[0]
    assert header[0] == "id"
    assert "yaratilgan (UTC+5)" in header


def test_the_export_never_leaks_a_capability(client):
    """To'lov kodi — tokenning bo'lagi: uni botga yuborgan odam sessiyani o'ziga oladi."""
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        payment_code, share_code = session.payment_code, session.share_code
    admin_login(client)

    body = client.get("/admin/export/sessions.csv").content.decode("utf-8-sig")
    for secret in (token, payment_code, share_code):
        assert secret and secret not in body


def test_payments_export_hides_the_receipt_file_id(client):
    """file_id + BOT_TOKEN = chek rasmi (karta raqami ko'rinadigan)."""
    token = complete_session(client)
    with db_session(client) as db:
        outcome = PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=777,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
        payment_id = outcome.payment.id
        PremiumPaymentService(db).attach_receipt(
            telegram_user_id=777,
            receipt_file_id="MAXFIY-FILE-ID",
            receipt_type="photo",
            payment_id=payment_id,
        )
    admin_login(client)

    body = client.get("/admin/export/payments.csv").content.decode("utf-8-sig")
    assert "MAXFIY-FILE-ID" not in body
    rows = _rows(client.get("/admin/export/payments.csv").content)
    header, first = rows[0], rows[1]
    assert first[header.index("chek_bor")] == "1"
    # Summa toza butun son bo'lishi kerak: "9 990" Excel'da matn bo'lib, yig'ilmaydi.
    assert first[header.index("summa")] == str(settings.premium_price)


def test_a_formula_planted_by_an_anonymous_visitor_is_neutralised(client):
    """`?source=` ni autentifikatsiyasiz har kim yozib ketishi mumkin."""
    client.get("/personality", params={"source": HOSTILE_SOURCE}, headers={"user-agent": "Mozilla/5.0"})
    admin_login(client)

    body = client.get("/admin/export/sessions.csv").content
    cells = _cells(body)
    assert f"'{HOSTILE_SOURCE}" in cells
    for cell in cells:
        assert not cell.startswith(("=", "+", "@")), cell


def test_negative_numbers_are_not_escaped_into_text():
    """Formuladan himoya faqat MATN ustunlariga tegishli.

    Aks holda manfiy summa `'-5000` bo'lib qolib, buxgalterning SUM() i xato berardi.
    """
    assert csv_export.int_cell(-5000) == "-5000"
    assert csv_export.text_cell("-5000") == "'-5000"


def test_a_tab_prefixed_formula_is_still_caught():
    # Excel import paytida boshidagi bo'sh joyni tashlaydi, shuning uchun tekshiruv
    # lstrip qilingan birinchi belgi bo'yicha.
    assert csv_export.text_cell("\t=HYPERLINK(1)").startswith("' =HYPERLINK")


def test_naive_timestamps_are_treated_as_utc():
    """SQLite ofsetni saqlamaydi — naive qiymat mahalliy vaqt deb o'qilsa 5 soat xato bo'lardi."""
    naive = datetime(2026, 8, 7, 20, 30)
    assert csv_export.date_cell(naive) == "2026-08-08 01:30:00"
    aware = datetime(2026, 8, 7, 20, 30, tzinfo=timezone.utc)
    assert csv_export.date_cell(aware) == csv_export.date_cell(naive)
    assert csv_export.date_cell(None) == ""


def test_an_unknown_filter_is_rejected_instead_of_exporting_everything(client):
    complete_session(client)
    admin_login(client)

    response = client.get("/admin/export/sessions.csv?filter=completedd")
    assert response.status_code == 400
    assert "filtr" in response.text.lower() or "filter" in response.text.lower()

    payments = client.get("/admin/export/payments.csv?filter=aproved")
    assert payments.status_code == 400


def test_a_date_window_narrows_the_export(client):
    complete_session(client)
    admin_login(client)

    empty = client.get("/admin/export/sessions.csv?date_from=2000-01-01&date_to=2000-01-02")
    assert empty.status_code == 200
    assert len(_rows(empty.content)) == 1  # faqat sarlavha

    bad = client.get("/admin/export/sessions.csv?date_from=07.08.2026")
    assert bad.status_code == 400


def test_a_too_large_export_asks_for_a_narrower_range(client, monkeypatch):
    complete_session(client)
    monkeypatch.setattr(settings, "export_max_rows", 0)
    admin_login(client)

    response = client.get("/admin/export/sessions.csv")
    assert response.status_code == 400
    assert "toraytiring" in response.text


def test_the_export_is_audited_with_the_row_count(client):
    from app.models.admin import AdminAuditLog

    complete_session(client)
    admin_login(client)
    client.get("/admin/export/sessions.csv?filter=completed")

    with db_session(client) as db:
        entry = db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "export_sessions"))
    assert entry is not None
    assert "filter=completed" in entry.detail
    assert "qator=1" in entry.detail


def test_payments_export_reflects_the_status_filter(client):
    token = complete_session(client)
    with db_session(client) as db:
        PremiumPaymentService(db).start_premium_from_deeplink(
            session_token=token,
            telegram_user_id=778,
            telegram_username="payer",
            telegram_first_name="Ali",
        )
    admin_login(client)

    pending = _rows(client.get("/admin/export/payments.csv?filter=pending").content)
    approved = _rows(client.get("/admin/export/payments.csv?filter=approved").content)
    assert len(pending) == 2
    assert len(approved) == 1

    with db_session(client) as db:
        assert db.scalar(select(PaymentRequest.status)) == "pending"


def test_an_out_of_range_year_is_a_400_not_a_500(client):
    """0001-01-01 ni UTC ga o'tkazish OverflowError beradi, u ValueError emas."""
    admin_login(client)
    response = client.get("/admin/export/sessions.csv?date_from=0001-01-01")
    assert response.status_code == 400
    assert client.get("/admin/export/sessions.csv?date_to=0001-01-01").status_code == 400


def test_the_audit_row_records_the_dates_the_admin_typed(client):
    """UTC lahzasini `.date()` bilan chiqarish bir kun oldingi sanani berardi."""
    from app.models.admin import AdminAuditLog

    complete_session(client)
    admin_login(client)
    client.get("/admin/export/sessions.csv?date_from=2026-08-07&date_to=2026-08-07")

    with db_session(client) as db:
        entry = db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "export_sessions"))
    assert "from=2026-08-07" in entry.detail
    # Yuqori chegara oraliqqa kirmaydi, lekin jurnalda ADMIN yozgan sana turishi kerak.
    assert "to=2026-08-07" in entry.detail

"""PDF hisobot: kirish nazorati, mazmuni va shrift qamrovi."""

from datetime import datetime, timezone

from app.models.personality import PersonalityTestSession
from app.pdf.result_report import (
    FONT_DIR,
    PdfDimension,
    PdfReport,
    build_result_pdf,
    fonts_available,
    pdf_filename,
)
from tests.helpers import complete_session, db_session, session_by_token


def _grant_premium(client, token: str) -> None:
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.is_premium = True
        db.commit()


def _sample_report() -> PdfReport:
    return PdfReport(
        brand="Xarakter testi",
        result_type="INFP",
        title="Ma’no izlovchi",
        short_description="Siz qadriyatlaringizga sodiqsiz.",
        strengths=["Chuqur empatiya", "Ijodiy fikrlash"],
        challenges=["Tanqidga sezgirlik"],
        dimensions=[PdfDimension("Introvert (I)", 70, "Ekstravert (E)", 30)],
        sections=[],
        strengths_label="Kuchli tomonlar",
        challenges_label="Qiyin tomonlar",
        dimensions_label="O‘lchovlar",
        footer_note="Bu tibbiy tashxis emas.",
        generated_label="Sana:",
        generated_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
    )


# --------------------------- shriftlar ---------------------------


def test_pdf_fonts_are_committed():
    """Shriftlar repoda bo'lishi shart — ish vaqtida yuklab olinmaydi."""
    assert (FONT_DIR / "Inter-Regular.ttf").exists()
    assert (FONT_DIR / "Inter-Bold.ttf").exists()
    assert fonts_available()


def test_fonts_cover_uzbek_and_cyrillic():
    """Kirill yoki tutuq belgisi yo'q shrift bilan hisobot o'qib bo'lmas holga keladi."""
    from fontTools.ttLib import TTFont

    codepoints: set[int] = set()
    font = TTFont(str(FONT_DIR / "Inter-Regular.ttf"))
    for table in font["cmap"].tables:
        codepoints.update(table.cmap.keys())
    font.close()

    for codepoint in (0x2018, 0x2019, 0x02BB, 0x0410, 0x044F, 0x0451):
        assert codepoint in codepoints, f"U+{codepoint:04X} yo'q"


# --------------------------- generator ---------------------------


def test_build_result_pdf_returns_a_valid_pdf():
    payload = build_result_pdf(_sample_report())
    assert payload is not None
    assert payload.startswith(b"%PDF-")
    assert payload.rstrip().endswith(b"%%EOF")
    assert len(payload) > 2000


def test_pdf_carries_the_title_metadata():
    payload = build_result_pdf(_sample_report())
    assert b"INFP" in payload


def test_pdf_filename_is_derived_from_the_type():
    assert pdf_filename("INFP") == "xarakter-testi-infp.pdf"


# --------------------------- marshrut ---------------------------


def test_pdf_requires_premium(client):
    token = complete_session(client)
    response = client.get(f"/personality/result/{token}/pdf", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/personality/result/{token}"


def test_pdf_is_served_after_premium_is_granted(client):
    token = complete_session(client)
    _grant_premium(client, token)

    response = client.get(f"/personality/result/{token}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_pdf_rejects_a_stranger(client):
    """Boshqa brauzer tokenni bilsa ham pullik hisobotni ololmaydi."""
    from fastapi.testclient import TestClient

    from app.main import app

    token = complete_session(client)
    _grant_premium(client, token)

    with TestClient(app) as stranger:
        response = stranger.get(f"/personality/result/{token}/pdf", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/personality"


def test_pdf_link_appears_only_for_premium(client):
    token = complete_session(client)
    assert f"/personality/result/{token}/pdf" not in client.get(f"/personality/result/{token}").text

    _grant_premium(client, token)
    assert f"/personality/result/{token}/pdf" in client.get(f"/personality/result/{token}").text


def test_pdf_is_generated_in_russian_too(client):
    token = complete_session(client)
    _grant_premium(client, token)

    response = client.get(f"/personality/result/{token}/pdf?lang=ru")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_pdf_contains_the_premium_sections(client):
    """Bepul sahifada yopiq bo'lgan bo'limlar PDFda bo'lishi kerak."""
    token = complete_session(client)
    _grant_premium(client, token)
    with db_session(client) as db:
        session: PersonalityTestSession = session_by_token(db, token)
        result_type = session.result_type

    payload = client.get(f"/personality/result/{token}/pdf").content

    assert result_type.encode() in payload
    # Sakkizta premium bo'lim ikkinchi sahifadan boshlanadi, ya'ni fayl bir sahifadan katta.
    assert payload.count(b"/Type /Page") >= 2 or payload.count(b"/Type/Page") >= 2


def test_the_queue_builds_a_pdf_document_for_a_premium_session(client):
    """Tasdiqlangach mijoz PDFni Telegramda oladi — brauzerga qaytishi shart emas."""
    from app.bot import messages

    token = complete_session(client)
    _grant_premium(client, token)

    with db_session(client) as db:
        session = session_by_token(db, token)
        built = messages.premium_pdf_message(db, session.id)

    assert built.document_name.endswith(".pdf")
    assert built.document_bytes.startswith(b"%PDF-")


def test_the_queue_cancels_the_pdf_for_a_non_premium_session(client):
    """Premium bekor qilingan bo'lsa qator bekor qilinadi, qayta urinilmaydi."""
    from app.bot import messages
    from app.models.enums import NotificationStatus

    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        built = messages.premium_pdf_message(db, session.id)

    assert built.status == NotificationStatus.CANCELLED.value


def test_missing_fonts_are_retried_instead_of_failing_forever(client, monkeypatch):
    """Shriftsiz yig'ilgan image butun navbatni "abadiy muvaffaqiyatsiz" qilmasligi kerak."""
    from app.bot import messages
    from app.pdf import result_report

    token = complete_session(client)
    _grant_premium(client, token)
    monkeypatch.setattr(result_report, "_register_fonts", lambda: False)

    with db_session(client) as db:
        session = session_by_token(db, token)
        built = messages.premium_pdf_message(db, session.id)

    # Terminal holat YO'Q — qator navbatda qoladi va shriftlar qaytarilgach yuboriladi.
    assert built.status is None
    assert "shrift" in (built.error or "").lower()

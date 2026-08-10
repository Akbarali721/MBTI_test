"""Natija PDF'ini yig'adi — veb marshruti ham, bot ham shu yerdan foydalanadi."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from app.i18n import DEFAULT as DEFAULT_LANG
from app.i18n import t
from app.models.personality import DEFAULT_CONTENT_LANGUAGE, PersonalityTestSession
from app.pdf.result_report import PdfDimension, PdfReport, PdfSection, build_result_pdf
from app.personality.share_code import share_code_for_session, share_path
from app.services import ai_advice_service
from app.services.personality_service import PersonalityService
from app.services.premium_report import build_premium_report

logger = logging.getLogger(__name__)


def build_report(db: Session, token: str, *, lang: str, base_url: str) -> PdfReport:
    resolved_lang = lang or DEFAULT_CONTENT_LANGUAGE
    session = PersonalityService(db).get_session_or_404(token)
    report = build_premium_report(db, session, language=resolved_lang)
    share_url = f"{base_url.rstrip('/')}{share_path(share_code_for_session(db, session))}"
    dimensions = [
        PdfDimension(
            left_label=t(f"dimension.{dim.left_key}", resolved_lang),
            left_percent=dim.left_percent,
            right_label=t(f"dimension.{dim.right_key}", resolved_lang),
            right_percent=dim.right_percent,
        )
        for dim in report.dimensions
    ]
    sections = [PdfSection(title=section.title, body=section.body) for section in report.sections]
    sections.extend(_advice_sections(db, report.session, resolved_lang))
    return PdfReport(
        brand=t("site.name", resolved_lang),
        result_type=report.result_type,
        title=report.title,
        short_description=report.short_description,
        strengths=report.strengths,
        challenges=report.challenges,
        dimensions=dimensions,
        sections=sections,
        strengths_label=t("result.strengths", resolved_lang),
        challenges_label=t("result.challenges", resolved_lang),
        dimensions_label=t("result.dimensions", resolved_lang),
        footer_note=t("result.disclaimer", resolved_lang),
        generated_label=t("pdf.generated", resolved_lang),
        generated_at=datetime.now(timezone.utc),
        share_url=share_url,
    )


def _advice_sections(db: Session, session: PersonalityTestSession, lang: str) -> list[PdfSection]:
    """AI maslahatlarini bitta bo'limga yig'adi.

    Matn ESCAPE qilinadi: reportlab `Paragraph` mini-XML o'qiydi va model javobidagi
    oddiy "&" yoki "<" belgisi butun hisobotni yiqitardi. Bazadagi kontent bizniki,
    bu matn esa tashqaridan keladi.
    """
    report = ai_advice_service.get_report(db, session.id, lang)
    items = ai_advice_service.items_from_report(report)
    if not items:
        return []
    lines = [
        f"<b>{number}. {escape(item.title)}</b><br/>{escape(item.body)}"
        for number, item in enumerate(items, start=1)
    ]
    return [PdfSection(title=t("ai.title", lang, count=len(items)), body="<br/><br/>".join(lines))]


class PdfNotPremium(Exception):
    """Sessiya premium emas — hisobot chiqarilmaydi (qayta urinishning ma'nosi yo'q)."""


class PdfFontsUnavailable(Exception):
    """Shriftlar yig'ilmada yo'q — bu deploy nuqsoni, vaqtinchalik xato deb qaraladi."""


def build_pdf_bytes(
    db: Session,
    token: str,
    *,
    lang: str = DEFAULT_LANG,
    base_url: str,
) -> bytes:
    """Ikki xil muvaffaqiyatsizlik ATAYLAB ajratilgan.

    Avval ikkalasi ham `None` qaytarardi. Natijada shriftsiz yig'ilgan bitta image
    butun navbatni bir necha soniyada "abadiy muvaffaqiyatsiz" qilib qo'yishi mumkin
    edi va uni premium bekor qilingan holatdan ajratib bo'lmasdi.
    """
    session = PersonalityService(db).get_session_or_404(token)
    if not session.is_premium:
        raise PdfNotPremium(token)
    payload = build_result_pdf(build_report(db, token, lang=lang, base_url=base_url))
    if payload is None:
        raise PdfFontsUnavailable(token)
    return payload

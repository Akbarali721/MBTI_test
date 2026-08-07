"""Natija PDF'ini yig'adi — veb marshruti ham, bot ham shu yerdan foydalanadi."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.i18n import DEFAULT as DEFAULT_LANG
from app.i18n import t
from app.models.personality import DEFAULT_CONTENT_LANGUAGE
from app.pdf.result_report import PdfDimension, PdfReport, PdfSection, build_result_pdf
from app.personality.share_code import share_code_for_session, share_path
from app.services.personality_service import PersonalityService

logger = logging.getLogger(__name__)

PREMIUM_SECTIONS: tuple[tuple[str, str], ...] = (
    ("result.section.motivation", "motivation_analysis"),
    ("result.section.work_style", "work_style"),
    ("result.section.career", "career_environment"),
    ("result.section.friendship", "friendship_style"),
    ("result.section.relationship", "relationship_needs"),
    ("result.section.compatible_people", "compatible_people"),
    ("result.section.difficult", "difficult_communication"),
    ("result.section.action_plan", "action_plan"),
)

_DIMENSION_POLES = (("ei", "i", "e"), ("sn", "s", "n"), ("tf", "t", "f"), ("jp", "j", "p"))


def build_report(db: Session, token: str, *, lang: str, base_url: str) -> PdfReport:
    service = PersonalityService(db)
    view = service.get_result_view(token, language=lang or DEFAULT_CONTENT_LANGUAGE)
    session, content, result = view["session"], view["content"], view["result"]

    share_url = f"{base_url.rstrip('/')}{share_path(share_code_for_session(db, session))}"
    dimensions = [
        PdfDimension(
            left_label=t(f"dimension.{left}", lang),
            left_percent=getattr(result, name).left_percent,
            right_label=t(f"dimension.{right}", lang),
            right_percent=getattr(result, name).right_percent,
        )
        for name, left, right in _DIMENSION_POLES
    ]
    sections = [
        PdfSection(title=t(key, lang), body=getattr(content, field))
        for key, field in PREMIUM_SECTIONS
        if getattr(content, field, None)
    ]
    return PdfReport(
        brand=t("site.name", lang),
        result_type=session.result_type or "",
        title=content.title,
        short_description=content.short_description,
        strengths=view["strengths"],
        challenges=view["challenges"],
        dimensions=dimensions,
        sections=sections,
        strengths_label=t("result.strengths", lang),
        challenges_label=t("result.challenges", lang),
        dimensions_label=t("result.dimensions", lang),
        footer_note=t("result.disclaimer", lang),
        generated_label=t("pdf.generated", lang),
        generated_at=datetime.now(timezone.utc),
        share_url=share_url,
    )


def build_pdf_bytes(
    db: Session,
    token: str,
    *,
    lang: str = DEFAULT_LANG,
    base_url: str,
) -> bytes | None:
    """Premium bo'lmagan sessiya uchun ham None qaytaradi — pullik kontent chetlab o'tilmasin."""
    session = PersonalityService(db).get_session_or_404(token)
    if not session.is_premium:
        return None
    return build_result_pdf(build_report(db, token, lang=lang, base_url=base_url))

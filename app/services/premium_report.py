"""Premium natija ma'lumotlari — HTML va PDF uchun bitta manba."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.i18n import DEFAULT as DEFAULT_LANG
from app.models.personality import PersonalityTestSession
from app.services.personality_service import PersonalityService
from app.services.premium_presentation import PremiumBlock, compose_premium_blocks

_DIMENSION_POLES = (("ei", "i", "e"), ("sn", "s", "n"), ("tf", "t", "f"), ("jp", "j", "p"))


@dataclass(frozen=True)
class PremiumDimension:
    name: str
    left_key: str
    right_key: str
    left_percent: int
    right_percent: int


@dataclass(frozen=True)
class PremiumReport:
    session: PersonalityTestSession
    result_type: str
    title: str
    short_description: str
    strengths: list[str]
    challenges: list[str]
    public_view: str
    dimensions: tuple[PremiumDimension, ...]
    blocks: tuple[PremiumBlock, ...]
    language: str


def build_premium_report(
    db: Session,
    session: PersonalityTestSession,
    *,
    language: str | None = None,
) -> PremiumReport:
    """MBTI premium kontentini shablon/PDF dan mustaqil strukturada qaytaradi."""
    lang = language or DEFAULT_LANG
    view = PersonalityService(db).get_result_view(session.token, language=lang)
    session_row = view["session"]
    content = view["content"]
    result = view["result"]

    dimensions = tuple(
        PremiumDimension(
            name=name,
            left_key=left,
            right_key=right,
            left_percent=getattr(result, name).left_percent,
            right_percent=getattr(result, name).right_percent,
        )
        for name, left, right in _DIMENSION_POLES
    )
    blocks = compose_premium_blocks(
        content,
        list(view["strengths"]),
        list(view["challenges"]),
        language=lang,
    )

    return PremiumReport(
        session=session_row,
        result_type=session_row.result_type or "",
        title=content.title,
        short_description=content.short_description,
        strengths=list(view["strengths"]),
        challenges=list(view["challenges"]),
        public_view=content.public_view or "",
        dimensions=dimensions,
        blocks=blocks,
        language=lang,
    )

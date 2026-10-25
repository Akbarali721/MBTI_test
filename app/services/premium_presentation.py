"""Premium natijani 6 ta qisqa, amaliy bo'limga yig'ish (DB o'zgarmaydi)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.i18n import t
from app.models.personality import PersonalityResultContent

MAX_WORDS_BODY = 90
MAX_WORDS_PARAGRAPH = 55
STRENGTH_COUNT = 3
DRAIN_COUNT = 3
ACTION_COUNT = 7
MAX_CAREER_EXAMPLES = 6


@dataclass(frozen=True)
class PremiumBlock:
    title_key: str
    title: str
    body: str | None = None
    bullets: tuple[str, ...] = ()
    sub_bullets: tuple[str, ...] = ()


def _words(text: str) -> list[str]:
    return re.findall(r"\S+", (text or "").strip())


def trim_words(text: str, limit: int = MAX_WORDS_BODY) -> str:
    parts = _words(text)
    if len(parts) <= limit:
        return " ".join(parts)
    return " ".join(parts[:limit]).rstrip(".,;:") + "…"


def first_sentences(text: str, count: int = 2) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    chunks = re.split(r"(?<=[.!?])\s+", cleaned)
    chosen = [c for c in chunks if c][:count]
    return " ".join(chosen)


def _lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _brief_summary(content: PersonalityResultContent) -> str:
    """Premium qisqa tavsif bepul «Siz qanday odamsiz?» matnini qaytarmaydi."""
    source = (content.motivation_analysis or "").strip()
    if len(_words(source)) < 20:
        extra = first_sentences(content.public_view or "", 1)
        source = " ".join(part for part in (source, extra) if part)
    return trim_words(source, MAX_WORDS_BODY)


def _strength_bullets(content: PersonalityResultContent, strengths: list[str]) -> tuple[str, ...]:
    """Uch qatorli public_view — kuchli tomonni qayerda ishlatish. Aks holda bepul ro‘yxat."""
    lines = _lines(content.public_view or "")
    if len(lines) >= STRENGTH_COUNT:
        return tuple(trim_words(line, 32) for line in lines[:STRENGTH_COUNT])
    return tuple(trim_words(item, 22) for item in strengths[:STRENGTH_COUNT])


def _drain_bullets(content: PersonalityResultContent, challenges: list[str]) -> tuple[str, ...]:
    """Uch qatorli difficult_communication — vaziyat va yechim. Aks holda qiyinchiliklar."""
    lines = _lines(content.difficult_communication or "")
    if len(lines) >= DRAIN_COUNT:
        return tuple(trim_words(line, 40) for line in lines[:DRAIN_COUNT])
    items = [trim_words(item, 28) for item in challenges[:DRAIN_COUNT]]
    if len(items) < 2 and content.difficult_communication:
        items.append(trim_words(first_sentences(content.difficult_communication, 1), 28))
    return tuple(items[:DRAIN_COUNT])


def _career_example_bullets(career: str) -> tuple[str, ...]:
    text = (career or "").strip()
    if not text:
        return ()
    tail = text.split(":", 1)[-1] if ":" in text else text
    tail = tail.split(".")[0]
    raw = re.split(r"[,;]| va ", tail)
    bullets = [trim_words(part, 8) for part in raw if part.strip()]
    bullets = [b for b in bullets if len(b) > 2]
    return tuple(bullets[:MAX_CAREER_EXAMPLES])


def _relationship_body(content: PersonalityResultContent) -> str:
    chunks = [
        trim_words(first_sentences(content.friendship_style or "", 2), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.relationship_needs or "", 2), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.compatible_people or "", 2), MAX_WORDS_PARAGRAPH),
    ]
    unique: list[str] = []
    for chunk in chunks:
        if chunk and chunk not in unique:
            unique.append(chunk)
    return "\n\n".join(unique[:3])


def _action_bullets(plan: str) -> tuple[str, ...]:
    text = (plan or "").strip()
    if not text:
        return ()
    parts = re.split(r"(?<=\.)\s+(?=\d+-kun:)", text)
    if len(parts) > 1:
        cleaned = [trim_words(p.strip().rstrip("."), 28) for p in parts if p.strip()]
        return tuple(cleaned[:ACTION_COUNT])
    parts = re.split(r"(?<=\.)\s+(?=\d+[-–]?(?:kun|hafta|Kun|Hafta))", text)
    if len(parts) <= 1:
        parts = re.split(r"\.\s+(?=[A-ZА-Я0-9«\"'])", text)
    if len(parts) <= 1:
        parts = re.split(r"\.\s+", text)
    cleaned = [trim_words(p.strip().rstrip("."), 28) for p in parts if p.strip()]
    if not cleaned:
        cleaned = [trim_words(text, 28)]
    return tuple(cleaned[:ACTION_COUNT])


def compose_premium_blocks(
    content: PersonalityResultContent,
    strengths: list[str],
    challenges: list[str],
    *,
    language: str,
    action_plan_override: str | None = None,
) -> tuple[PremiumBlock, ...]:
    lang = language
    career_examples = _career_example_bullets(content.career_environment or "")
    work_intro = trim_words(first_sentences(content.work_style or "", 3), MAX_WORDS_BODY)

    return (
        PremiumBlock(
            title_key="result.premium.brief",
            title=t("result.premium.brief", lang),
            body=_brief_summary(content),
        ),
        PremiumBlock(
            title_key="result.premium.strengths",
            title=t("result.premium.strengths", lang),
            bullets=_strength_bullets(content, strengths),
        ),
        PremiumBlock(
            title_key="result.premium.drains",
            title=t("result.premium.drains", lang),
            bullets=_drain_bullets(content, challenges),
        ),
        PremiumBlock(
            title_key="result.premium.work",
            title=t("result.premium.work", lang),
            body=work_intro,
            sub_bullets=career_examples,
        ),
        PremiumBlock(
            title_key="result.premium.relationships",
            title=t("result.premium.relationships", lang),
            body=_relationship_body(content),
        ),
        PremiumBlock(
            title_key="result.premium.actions",
            title=t("result.premium.actions", lang),
            bullets=_action_bullets(action_plan_override or content.action_plan or ""),
        ),
    )

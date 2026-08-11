"""Premium natijani 6 ta qisqa, amaliy bo'limga yig'ish (DB o'zgarmaydi)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.i18n import t
from app.models.personality import PersonalityResultContent

MAX_WORDS_BODY = 60
MAX_WORDS_PARAGRAPH = 45
STRENGTH_COUNT = 3
DRAIN_COUNT = 3
ACTION_COUNT = 3
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


def _brief_summary(content: PersonalityResultContent) -> str:
    parts = [first_sentences(content.short_description or "", 2)]
    extra = first_sentences(content.motivation_analysis or "", 1)
    if extra and extra not in parts[0]:
        parts.append(extra)
    combined = " ".join(p for p in parts if p).strip()
    return trim_words(combined, 55)


def _drain_bullets(content: PersonalityResultContent, challenges: list[str]) -> tuple[str, ...]:
    items: list[str] = []
    for item in challenges[:DRAIN_COUNT]:
        items.append(trim_words(item, 22))
    if len(items) < 2 and content.difficult_communication:
        items.append(trim_words(first_sentences(content.difficult_communication, 1), 22))
    if len(items) < 2 and content.motivation_analysis:
        items.append(trim_words(first_sentences(content.motivation_analysis, 1), 22))
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
        trim_words(first_sentences(content.friendship_style or "", 1), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.compatible_people or "", 1), MAX_WORDS_PARAGRAPH),
        trim_words(first_sentences(content.difficult_communication or "", 1), MAX_WORDS_PARAGRAPH),
    ]
    if content.relationship_needs:
        chunks.insert(
            1,
            trim_words(first_sentences(content.relationship_needs, 1), MAX_WORDS_PARAGRAPH),
        )
    unique: list[str] = []
    for chunk in chunks:
        if chunk and chunk not in unique:
            unique.append(chunk)
    return "\n\n".join(unique[:3])


def _action_bullets(plan: str) -> tuple[str, ...]:
    text = (plan or "").strip()
    if not text:
        return ()
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
) -> tuple[PremiumBlock, ...]:
    lang = language
    career_examples = _career_example_bullets(content.career_environment or "")
    work_intro = trim_words(
        " ".join(
            filter(
                None,
                [
                    first_sentences(content.work_style or "", 1),
                    first_sentences(content.career_environment or "", 1).split(":")[0]
                    if ":" in (content.career_environment or "")
                    else "",
                ],
            )
        ),
        MAX_WORDS_BODY,
    )

    return (
        PremiumBlock(
            title_key="result.premium.brief",
            title=t("result.premium.brief", lang),
            body=_brief_summary(content),
        ),
        PremiumBlock(
            title_key="result.premium.strengths",
            title=t("result.premium.strengths", lang),
            bullets=tuple(trim_words(s, 14) for s in strengths[:STRENGTH_COUNT]),
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
            bullets=_action_bullets(content.action_plan or ""),
        ),
    )

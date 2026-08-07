"""Savol va natija kontentini bazaga yuklash.

Kontent joyida (order_number / (type, language) bo'yicha) yangilanadi — savol va variant
id lari saqlanadi, shuning uchun foydalanuvchi javoblari hech qachon avtomatik o'chmaydi.
"""

import json
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalityDimension
from app.models.personality import (
    DEFAULT_CONTENT_LANGUAGE,
    DEFAULT_VARIANT,
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityResultContent,
)
from app.seed.personality_questions_uz import PERSONALITY_QUESTIONS_UZ
from app.seed.personality_results_ru import get_result_copy_ru
from app.seed.personality_results_uz import ResultCopy, get_result_copy

# Har til uchun matn manbai. Yangi til qo'shish = shu yerga bitta qator.
RESULT_COPY_PROVIDERS: dict[str, Callable[[str], ResultCopy]] = {
    DEFAULT_CONTENT_LANGUAGE: get_result_copy,
    "ru": get_result_copy_ru,
}
# "uz" birinchi bo'lishi kerak: qolgan tillar topilmasa unga qaytiladi.
SEED_LANGUAGES: tuple[str, ...] = (
    DEFAULT_CONTENT_LANGUAGE,
    *(code for code in RESULT_COPY_PROVIDERS if code != DEFAULT_CONTENT_LANGUAGE),
)

ALL_TYPES = [
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
]

DIMENSIONS_CYCLE = [
    PersonalityDimension.EI,
    PersonalityDimension.SN,
    PersonalityDimension.TF,
    PersonalityDimension.JP,
]

SCORE_KEYS = ("e", "i", "s", "n", "t", "f", "j", "p")

# Har savolning 4 varianti gradient tartibida: dastlabki ikkitasi chap qutb,
# keyingi ikkitasi o'ng qutb (masalan E, E, I, I).
DIMENSION_POLES: dict[PersonalityDimension, tuple[str, str]] = {
    PersonalityDimension.EI: ("e", "i"),
    PersonalityDimension.SN: ("s", "n"),
    PersonalityDimension.TF: ("t", "f"),
    PersonalityDimension.JP: ("j", "p"),
}

OPTIONS_PER_QUESTION = 4


def _option_scores(dimension: PersonalityDimension, option_index: int) -> dict[str, int]:
    scores = {key: 0 for key in SCORE_KEYS}
    left, right = DIMENSION_POLES[dimension]
    scores[left if option_index < OPTIONS_PER_QUESTION // 2 else right] = 1
    return scores


def questions_are_empty(db: Session, variant: str = DEFAULT_VARIANT) -> bool:
    count = db.scalar(
        select(func.count()).select_from(PersonalityQuestion).where(PersonalityQuestion.variant == variant)
    )
    return int(count or 0) == 0


def results_are_empty(db: Session, language: str = DEFAULT_CONTENT_LANGUAGE) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(PersonalityResultContent)
        .where(PersonalityResultContent.language == language)
    )
    return int(count or 0) == 0


def _option_is_answered(db: Session, option_id: int) -> bool:
    stmt = select(func.count()).select_from(PersonalityAnswer).where(PersonalityAnswer.option_id == option_id)
    return int(db.scalar(stmt) or 0) > 0


def _sync_options(db: Session, question: PersonalityQuestion, option_texts: list[str]) -> None:
    existing = {opt.order_number: opt for opt in question.options}
    for index, text in enumerate(option_texts):
        order = index + 1
        scores = _option_scores(question.dimension, index)
        option = existing.pop(order, None)
        if option is None:
            option = PersonalityOption(question_id=question.id, text=text, order_number=order)
            db.add(option)
        else:
            option.text = text
        for key in SCORE_KEYS:
            setattr(option, f"{key}_score", scores[key])

    # Ortiqcha variantlar faqat ularga javob berilmagan bo'lsa o'chiriladi.
    for option in existing.values():
        if option.id is not None and _option_is_answered(db, option.id):
            continue
        db.delete(option)


def _sync_questions(db: Session, variant: str = DEFAULT_VARIANT) -> int:
    stmt = select(PersonalityQuestion).where(PersonalityQuestion.variant == variant)
    existing = {question.order_number: question for question in db.scalars(stmt).unique().all()}
    for order, (text, dimension, option_texts) in enumerate(PERSONALITY_QUESTIONS_UZ, start=1):
        question = existing.pop(order, None)
        if question is None:
            question = PersonalityQuestion(
                text=text, dimension=dimension, order_number=order, variant=variant, is_active=True
            )
            db.add(question)
            db.flush()
        else:
            question.text = text
            question.dimension = dimension
            question.is_active = True
        _sync_options(db, question, option_texts)

    # Kontentdan chiqib ketgan savollar o'chirilmaydi, faqat nofaol qilinadi.
    for question in existing.values():
        question.is_active = False

    db.flush()
    return len(PERSONALITY_QUESTIONS_UZ)


def seed_personality_questions(db: Session, *, force: bool = False, variant: str = DEFAULT_VARIANT) -> int:
    """Savollarni yuklaydi. force=False bo'lsa faqat to'plam bo'sh bo'lganda ishlaydi.

    A/B test uchun: `--variant B` bilan yuklab, so'ng B to'plamini tahrirlash mumkin —
    A to'plamiga tegilmaydi.
    """
    if not force and not questions_are_empty(db, variant):
        return 0
    count = _sync_questions(db, variant)
    db.commit()
    return count


def _result_rows(db: Session, language: str) -> dict[str, PersonalityResultContent]:
    stmt = select(PersonalityResultContent).where(PersonalityResultContent.language == language)
    return {row.personality_type: row for row in db.scalars(stmt).all()}


def result_copy_provider(language: str) -> Callable[[str], ResultCopy]:
    provider = RESULT_COPY_PROVIDERS.get(language)
    if provider is None:
        supported = ", ".join(sorted(RESULT_COPY_PROVIDERS))
        raise ValueError(f"'{language}' tili uchun natija matnlari yo'q (mavjud: {supported})")
    return provider


def _sync_results(db: Session, language: str) -> int:
    provider = result_copy_provider(language)
    existing = _result_rows(db, language)
    for ptype in ALL_TYPES:
        copy = provider(ptype)
        row = existing.get(ptype)
        if row is None:
            row = PersonalityResultContent(personality_type=ptype, language=language)
            db.add(row)
        row.title = copy["title"]
        row.short_description = copy["short_description"]
        row.free_strengths = json.dumps(copy["strengths"], ensure_ascii=False)
        row.free_challenges = json.dumps(copy["challenges"], ensure_ascii=False)
        row.public_view = copy["public_view"]
        row.motivation_analysis = copy["motivation_analysis"]
        row.work_style = copy["work_style"]
        row.career_environment = copy["career_environment"]
        row.friendship_style = copy["friendship_style"]
        row.relationship_needs = copy["relationship_needs"]
        row.compatible_people = copy["compatible_people"]
        row.difficult_communication = copy["difficult_communication"]
        row.action_plan = copy["action_plan"]
        row.is_active = True
    db.flush()
    return len(ALL_TYPES)


def seed_personality_results(
    db: Session, *, force: bool = False, language: str = DEFAULT_CONTENT_LANGUAGE
) -> int:
    """Natija kontentini yuklaydi. force=False bo'lsa faqat kontent yo'q bo'lganda ishlaydi."""
    # Noto'g'ri til kodi jimgina 0 qaytarmasin, darrov xato bersin.
    result_copy_provider(language)
    if not force and not results_are_empty(db, language):
        return 0
    count = _sync_results(db, language)
    db.commit()
    return count

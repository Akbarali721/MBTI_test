import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.personality import (
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityResultContent,
)
from app.seed.personality_questions_uz import PERSONALITY_QUESTIONS_UZ
from app.seed.personality_results_uz import get_result_copy
from app.models.enums import PersonalityDimension

ALL_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ",
]

DIMENSIONS_CYCLE = [
    PersonalityDimension.EI,
    PersonalityDimension.SN,
    PersonalityDimension.TF,
    PersonalityDimension.JP,
]


def _option_scores(dimension: PersonalityDimension, option_index: int) -> dict[str, int]:
    scores = {k: 0 for k in ("e", "i", "s", "n", "t", "f", "j", "p")}
    mapping = {
        PersonalityDimension.EI: [("e", "i"), ("i", "e"), ("e", "i"), ("i", "e")],
        PersonalityDimension.SN: [("s", "n"), ("n", "s"), ("s", "n"), ("n", "s")],
        PersonalityDimension.TF: [("t", "f"), ("f", "t"), ("t", "f"), ("f", "t")],
        PersonalityDimension.JP: [("j", "p"), ("p", "j"), ("j", "p"), ("p", "j")],
    }
    left, right = mapping[dimension][option_index]
    scores[left] = 1
    return scores


def _is_placeholder_data(db: Session) -> bool:
    row = db.scalar(
        select(PersonalityQuestion)
        .where(PersonalityQuestion.is_active.is_(True))
        .order_by(PersonalityQuestion.order_number)
        .limit(1)
    )
    if not row:
        return True
    text = row.text or ""
    return "[Placeholder]" in text or "placeholder javob" in text.lower()


def _clear_questions(db: Session) -> None:
    db.execute(delete(PersonalityAnswer))
    db.execute(delete(PersonalityOption))
    db.execute(delete(PersonalityQuestion))
    db.commit()


def _insert_uz_questions(db: Session) -> None:
    for order, (q_text, dimension, options) in enumerate(PERSONALITY_QUESTIONS_UZ, start=1):
        question = PersonalityQuestion(
            text=q_text,
            dimension=dimension,
            order_number=order,
            is_active=True,
        )
        db.add(question)
        db.flush()
        for idx, opt_text in enumerate(options):
            scores = _option_scores(dimension, idx)
            db.add(
                PersonalityOption(
                    question_id=question.id,
                    text=opt_text,
                    order_number=idx + 1,
                    e_score=scores["e"],
                    i_score=scores["i"],
                    s_score=scores["s"],
                    n_score=scores["n"],
                    t_score=scores["t"],
                    f_score=scores["f"],
                    j_score=scores["j"],
                    p_score=scores["p"],
                )
            )
    db.commit()


def seed_personality_questions(db: Session) -> None:
    if _is_placeholder_data(db):
        _clear_questions(db)
        _insert_uz_questions(db)


def _is_placeholder_result_row(row: PersonalityResultContent | None) -> bool:
    if not row:
        return True
    blob = " ".join(
        [
            row.title or "",
            row.short_description or "",
            row.free_strengths or "",
            row.public_view or "",
        ]
    ).lower()
    return "placeholder" in blob


def _clear_results(db: Session) -> None:
    db.execute(delete(PersonalityResultContent))
    db.commit()


def _insert_uz_results(db: Session) -> None:
    for ptype in ALL_TYPES:
        copy = get_result_copy(ptype)
        db.add(
            PersonalityResultContent(
                personality_type=ptype,
                title=copy["title"],
                short_description=copy["short_description"],
                free_strengths=json.dumps(copy["strengths"], ensure_ascii=False),
                free_challenges=json.dumps(copy["challenges"], ensure_ascii=False),
                public_view=copy["public_view"],
                motivation_analysis=copy["motivation_analysis"],
                work_style=copy["work_style"],
                career_environment=copy["career_environment"],
                friendship_style=copy["friendship_style"],
                relationship_needs=copy["relationship_needs"],
                compatible_people=copy["compatible_people"],
                difficult_communication=copy["difficult_communication"],
                action_plan=copy["action_plan"],
                is_active=True,
            )
        )
    db.commit()


def seed_personality_results(db: Session) -> None:
    row = db.scalar(
        select(PersonalityResultContent)
        .order_by(PersonalityResultContent.personality_type)
        .limit(1)
    )
    if row is None:
        _insert_uz_results(db)
        return
    if _is_placeholder_result_row(row):
        _clear_results(db)
        _insert_uz_results(db)


def seed_placeholder_results(db: Session) -> None:
    """Backward-compatible alias."""
    seed_personality_results(db)

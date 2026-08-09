"""Stratified random draw of 24 questions from the active bank (48 by default)."""

from __future__ import annotations

import random
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import PersonalityDimension, PersonalitySessionStatus
from app.models.personality import (
    DEFAULT_VARIANT,
    PersonalityAnswer,
    PersonalityQuestion,
    PersonalitySessionQuestion,
    PersonalityTestSession,
)
from app.personality.constants import (
    DIRECTION_BALANCE_PER_DIMENSION,
    MAX_CONSECUTIVE_SAME_DIMENSION,
    QUESTIONS_PER_DIMENSION,
    SESSION_QUESTION_COUNT,
)
from app.seed.personality_placeholders import DIMENSION_POLES

_DIMENSIONS = (
    PersonalityDimension.EI,
    PersonalityDimension.SN,
    PersonalityDimension.TF,
    PersonalityDimension.JP,
)


def session_rng(session: PersonalityTestSession) -> random.Random:
    """Deterministic per session token; different sessions get different draws."""
    return random.Random(session.token)


def validate_session_question_selection(questions: list[PersonalityQuestion]) -> None:
    """Hard guards: 24 unique IDs and no repeated stem text in one session."""
    ids = [question.id for question in questions]
    assert len(ids) == SESSION_QUESTION_COUNT
    assert len(set(ids)) == SESSION_QUESTION_COUNT
    texts = [question.text for question in questions]
    assert len(set(texts)) == SESSION_QUESTION_COUNT


def _group_by_stem_text(pool: list[PersonalityQuestion]) -> dict[str, list[PersonalityQuestion]]:
    groups: dict[str, list[PersonalityQuestion]] = {}
    for question in pool:
        groups.setdefault(question.text, []).append(question)
    return groups


def _pick_balanced_from_stem_pairs(
    groups: dict[str, list[PersonalityQuestion]],
    *,
    left_pole: str,
    per_direction: int,
    rng: random.Random,
) -> list[PersonalityQuestion]:
    """One question per stem; exactly per_direction left-pole and per_direction right-pole variants."""
    expected_stems = per_direction * 2
    if len(groups) != expected_stems:
        raise ValueError(f"Expected {expected_stems} stems, have {len(groups)}")
    if not all(len(variants) == 2 for variants in groups.values()):
        raise ValueError("Stem groups must contain exactly two bank variants")

    texts = list(groups.keys())
    rng.shuffle(texts)
    left_texts = texts[:per_direction]
    right_texts = texts[per_direction : per_direction * 2]

    chosen: list[PersonalityQuestion] = []
    for text in left_texts:
        variants = groups[text]
        match = next((q for q in variants if q.primary_pole == left_pole), None)
        if match is None:
            raise ValueError(f"No left-pole variant for stem {text!r}")
        chosen.append(match)
    for text in right_texts:
        variants = groups[text]
        match = next((q for q in variants if q.primary_pole != left_pole), None)
        if match is None:
            raise ValueError(f"No right-pole variant for stem {text!r}")
        chosen.append(match)
    return chosen


def _pick_balanced(
    pool: list[PersonalityQuestion],
    *,
    left_pole: str,
    count: int,
    per_direction: int,
    rng: random.Random,
) -> list[PersonalityQuestion]:
    groups = _group_by_stem_text(pool)
    if len(groups) == per_direction * 2 and all(len(variants) == 2 for variants in groups.values()):
        chosen = _pick_balanced_from_stem_pairs(
            groups,
            left_pole=left_pole,
            per_direction=per_direction,
            rng=rng,
        )
        if len(chosen) != count:
            raise ValueError("Unexpected selection size")
        return chosen

    toward_left = [q for q in pool if q.primary_pole == left_pole]
    toward_right = [q for q in pool if q.primary_pole != left_pole]
    if len(toward_left) < per_direction or len(toward_right) < per_direction:
        raise ValueError(
            f"Not enough questions for pole balance: need {per_direction}+{per_direction}, "
            f"have {len(toward_left)}+{len(toward_right)}"
        )
    chosen = rng.sample(toward_left, per_direction) + rng.sample(toward_right, per_direction)
    if len(chosen) != count:
        raise ValueError("Unexpected selection size")
    texts = [q.text for q in chosen]
    if len(set(texts)) != len(texts):
        raise ValueError("Duplicate stem text in selection")
    return chosen


def _has_long_dimension_run(questions: list[PersonalityQuestion], max_run: int) -> bool:
    run = 0
    prev: PersonalityDimension | None = None
    for question in questions:
        if question.dimension == prev:
            run += 1
            if run >= max_run:
                return True
        else:
            prev = question.dimension
            run = 1
    return False


def _shuffle_with_dimension_cap(
    questions: list[PersonalityQuestion],
    *,
    rng: random.Random,
    max_run: int = MAX_CONSECUTIVE_SAME_DIMENSION,
) -> list[PersonalityQuestion]:
    items = list(questions)
    for _ in range(500):
        rng.shuffle(items)
        if not _has_long_dimension_run(items, max_run + 1):
            return items
    # Greedy fallback: round-robin by dimension buckets, then shuffle within ties.
    by_dim: dict[PersonalityDimension, list[PersonalityQuestion]] = {d: [] for d in _DIMENSIONS}
    for q in questions:
        by_dim[q.dimension].append(q)
    for bucket in by_dim.values():
        rng.shuffle(bucket)
    merged: list[PersonalityQuestion] = []
    while len(merged) < len(questions):
        for dim in _DIMENSIONS:
            if by_dim[dim]:
                merged.append(by_dim[dim].pop())
    if _has_long_dimension_run(merged, max_run + 1):
        rng.shuffle(merged)
    return merged


def select_session_questions(
    db: Session,
    session: PersonalityTestSession,
    *,
    variant: str = DEFAULT_VARIANT,
    rng: random.Random | None = None,
) -> list[PersonalityQuestion]:
    """Pick 6×4 stratified questions, balance primary pole, shuffle order."""
    generator = rng or session_rng(session)
    stmt = (
        select(PersonalityQuestion)
        .where(
            PersonalityQuestion.is_active.is_(True),
            PersonalityQuestion.variant == variant,
        )
        .options(joinedload(PersonalityQuestion.options))
    )
    bank = list(db.scalars(stmt).unique().all())
    by_dimension: dict[PersonalityDimension, list[PersonalityQuestion]] = {d: [] for d in _DIMENSIONS}
    for question in bank:
        by_dimension[question.dimension].append(question)

    selected: list[PersonalityQuestion] = []
    for dimension in _DIMENSIONS:
        pool = by_dimension[dimension]
        if len(pool) < QUESTIONS_PER_DIMENSION:
            raise ValueError(
                f"Question bank too small for {dimension.value}: "
                f"need at least {QUESTIONS_PER_DIMENSION} active in variant {variant!r}, "
                f"have {len(pool)} (run `python -m app.seed` after migrations)"
            )
        left_pole, _right_pole = DIMENSION_POLES[dimension]
        selected.extend(
            _pick_balanced(
                pool,
                left_pole=left_pole,
                count=QUESTIONS_PER_DIMENSION,
                per_direction=DIRECTION_BALANCE_PER_DIMENSION,
                rng=generator,
            )
        )

    if len(selected) != SESSION_QUESTION_COUNT:
        raise ValueError("Selection must contain 24 questions")
    validate_session_question_selection(selected)

    ordered = _shuffle_with_dimension_cap(selected, rng=generator)
    validate_session_question_selection(ordered)
    return ordered


def persist_session_questions(
    db: Session,
    session: PersonalityTestSession,
    questions: list[PersonalityQuestion],
) -> None:
    validate_session_question_selection(questions)
    for index, question in enumerate(questions):
        db.add(
            PersonalitySessionQuestion(
                session_id=session.id,
                question_id=question.id,
                display_order=index,
            )
        )
    db.flush()


def _load_linked_questions(
    db: Session,
    session_id: int,
) -> list[PersonalityQuestion] | None:
    """Load persisted order via link rows only (avoids join row multiplication)."""
    link_stmt = (
        select(PersonalitySessionQuestion)
        .where(PersonalitySessionQuestion.session_id == session_id)
        .order_by(PersonalitySessionQuestion.display_order)
    )
    links = list(db.scalars(link_stmt).all())
    if not links:
        return None
    question_ids = [link.question_id for link in links]
    assert len(question_ids) == len(set(question_ids)), "duplicate question_id in session links"
    assert len(question_ids) == SESSION_QUESTION_COUNT, "session must have 24 linked questions"
    orders = [link.display_order for link in links]
    assert len(orders) == len(set(orders)), "duplicate display_order in session links"
    assert set(orders) == set(range(SESSION_QUESTION_COUNT)), "display_order must be 0..23"

    question_stmt = (
        select(PersonalityQuestion)
        .where(PersonalityQuestion.id.in_(question_ids))
        .options(joinedload(PersonalityQuestion.options))
    )
    loaded = {question.id: question for question in db.scalars(question_stmt).unique().all()}
    ordered = [loaded[qid] for qid in question_ids]
    if len(ordered) != len(question_ids):
        raise ValueError("Missing question rows for persisted session selection")
    validate_session_question_selection(ordered)
    return ordered


def _legacy_questions_from_answers(
    db: Session,
    session: PersonalityTestSession,
) -> list[PersonalityQuestion] | None:
    """Sessions that started before per-session selection: infer list from saved answers."""
    stmt = (
        select(PersonalityQuestion)
        .join(PersonalityAnswer, PersonalityAnswer.question_id == PersonalityQuestion.id)
        .where(PersonalityAnswer.session_id == session.id)
        .options(joinedload(PersonalityQuestion.options))
        .order_by(PersonalityQuestion.order_number, PersonalityQuestion.id)
    )
    seen: set[int] = set()
    ordered: list[PersonalityQuestion] = []
    for question in db.scalars(stmt).unique().all():
        if question.id in seen:
            continue
        seen.add(question.id)
        ordered.append(question)
    if not ordered:
        return None
    if session.status == PersonalitySessionStatus.COMPLETED:
        if len(ordered) != SESSION_QUESTION_COUNT:
            return None
        return ordered
    # In-progress legacy test: fixed variant order (pre-48-bank draw).
    if len(ordered) < SESSION_QUESTION_COUNT:
        variant_rows = (
            select(PersonalityQuestion)
            .where(
                PersonalityQuestion.is_active.is_(True),
                PersonalityQuestion.variant == session.variant,
            )
            .options(joinedload(PersonalityQuestion.options))
            .order_by(PersonalityQuestion.order_number)
            .limit(SESSION_QUESTION_COUNT)
        )
        legacy_full = list(db.scalars(variant_rows).unique().all())
        if len(legacy_full) == SESSION_QUESTION_COUNT:
            return legacy_full
    return None


def ensure_session_questions(
    db: Session,
    session: PersonalityTestSession,
    *,
    variant: str | None = None,
    rng: random.Random | None = None,
) -> list[PersonalityQuestion]:
    """Return persisted order; create selection on first call."""
    existing = _load_linked_questions(db, session.id)
    if existing is not None:
        return existing

    legacy = _legacy_questions_from_answers(db, session)
    if legacy is not None:
        validate_session_question_selection(legacy)
        with db.begin_nested():
            persist_session_questions(db, session, legacy)
        reloaded = _load_linked_questions(db, session.id)
        return reloaded if reloaded is not None else legacy

    chosen = select_session_questions(
        db,
        session,
        variant=variant or session.variant,
        rng=rng,
    )
    with db.begin_nested():
        persist_session_questions(db, session, chosen)
    reloaded = _load_linked_questions(db, session.id)
    return reloaded if reloaded is not None else chosen


def selection_dimension_counts(questions: list[PersonalityQuestion]) -> Counter[PersonalityDimension]:
    return Counter(q.dimension for q in questions)


def selection_primary_pole_counts(
    questions: list[PersonalityQuestion],
) -> dict[PersonalityDimension, Counter[str]]:
    out: dict[PersonalityDimension, Counter[str]] = {d: Counter() for d in _DIMENSIONS}
    for question in questions:
        out[question.dimension][question.primary_pole] += 1
    return out

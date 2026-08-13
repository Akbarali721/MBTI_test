"""Stratified 24-question selection and completion guards."""

from __future__ import annotations

import random

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.enums import PersonalityDimension
from app.models.personality import PersonalityQuestion, PersonalitySessionQuestion
from app.personality.constants import QUESTIONS_PER_DIMENSION, SESSION_QUESTION_COUNT
from app.personality.question_selection import (
    ensure_session_questions,
    selection_dimension_counts,
    selection_primary_pole_counts,
    session_rng,
    validate_session_question_selection,
)
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import DIMENSION_POLES, PERSONALITY_QUESTIONS_BANK
from app.services.personality_service import PersonalityService
from tests.helpers import complete_session, db_session, session_by_token, start_session


def _favor_left_option_index(question: PersonalityQuestion) -> int:
    left, _right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == left else 3


def _favor_right_option_index(question: PersonalityQuestion) -> int:
    _left, right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == right else 3


def test_question_bank_has_forty_eight_active(client):
    with db_session(client) as db:
        from app.seed.personality_placeholders import question_bank_is_valid, question_bank_stats

        assert question_bank_is_valid(db, "A")
        stats = question_bank_stats(db, "A")
        assert stats["active_total"] == len(PERSONALITY_QUESTIONS_BANK) == 48


def test_session_draws_twenty_four_balanced(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="test")
        questions = ensure_session_questions(db, session, rng=random.Random("draw"))
        validate_session_question_selection(questions)
        assert len(questions) == SESSION_QUESTION_COUNT
        assert len({q.id for q in questions}) == SESSION_QUESTION_COUNT
        assert len({q.text for q in questions}) == SESSION_QUESTION_COUNT

        counts = selection_dimension_counts(questions)
        assert counts[PersonalityDimension.EI] == QUESTIONS_PER_DIMENSION
        assert counts[PersonalityDimension.SN] == QUESTIONS_PER_DIMENSION
        assert counts[PersonalityDimension.TF] == QUESTIONS_PER_DIMENSION
        assert counts[PersonalityDimension.JP] == QUESTIONS_PER_DIMENSION

        pole_counts = selection_primary_pole_counts(questions)
        for dimension in (
            PersonalityDimension.EI,
            PersonalityDimension.SN,
            PersonalityDimension.TF,
            PersonalityDimension.JP,
        ):
            left, right = DIMENSION_POLES[dimension]
            assert pole_counts[dimension][left] == 3
            assert pole_counts[dimension][right] == 3


def test_same_session_keeps_selection_after_reload(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="test")
        first = ensure_session_questions(db, session, rng=random.Random("stable"))
        db.commit()
        db.expire_all()
        again = ensure_session_questions(db, session)
        assert [q.id for q in first] == [q.id for q in again]


def test_different_sessions_can_differ(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        a = repo.create_session(source="test")
        b = repo.create_session(source="test")
        ids_a = [q.id for q in ensure_session_questions(db, a, rng=session_rng(a))]
        ids_b = [q.id for q in ensure_session_questions(db, b, rng=session_rng(b))]
        assert ids_a != ids_b


def test_no_more_than_two_consecutive_same_dimension(client):
    with db_session(client) as db:
        session = PersonalityRepository(db).create_session(source="test")
        questions = ensure_session_questions(db, session, rng=random.Random("shuffle"))
        run = 0
        prev = None
        for question in questions:
            if question.dimension == prev:
                run += 1
                assert run < 3
            else:
                prev = question.dimension
                run = 1


def test_incomplete_session_cannot_complete(client):
    token = start_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        service = PersonalityService(db)
        questions = service.repo.get_session_questions_ordered(session)
        q0 = questions[0]
        opt = sorted(q0.options, key=lambda o: o.order_number)[0]
        with pytest.raises(HTTPException):
            service.submit_answer(
                token,
                question_id=q0.id,
                option_id=opt.id,
                question_index=len(questions) - 1,
            )


def test_cannot_complete_with_skipped_questions(client):
    token = start_session(client)
    with db_session(client) as db:
        service = PersonalityService(db)
        session = session_by_token(db, token)
        questions = service.repo.get_session_questions_ordered(session)
        last = questions[-1]
        opt = sorted(last.options, key=lambda o: o.order_number)[0]
        with pytest.raises(HTTPException):
            service.submit_answer(
                token,
                question_id=last.id,
                option_id=opt.id,
                question_index=len(questions) - 1,
            )


def test_favor_left_vs_right_types_are_opposites(client):
    left_token = complete_session(client, option_picker=_favor_left_option_index)
    client.cookies.clear()
    right_token = complete_session(client, option_picker=_favor_right_option_index)
    with db_session(client) as db:
        left = session_by_token(db, left_token).result_type
        right = session_by_token(db, right_token).result_type
    assert left and right
    pairs = {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}
    assert right == "".join(pairs[c] for c in left)


def test_persisted_session_question_rows(client):
    token = start_session(client)
    assert client.get(f"/personality/test/{token}?q=0").status_code == 200
    with db_session(client) as db:
        session = session_by_token(db, token)
        count = db.scalar(
            select(func.count())
            .select_from(PersonalitySessionQuestion)
            .where(PersonalitySessionQuestion.session_id == session.id)
        )
        assert count == SESSION_QUESTION_COUNT


def test_hundred_sessions_have_unique_ids_and_stems(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        for seed in range(100):
            session = repo.create_session(source="stress")
            questions = ensure_session_questions(db, session, rng=random.Random(seed))
            validate_session_question_selection(questions)
            counts = selection_dimension_counts(questions)
            assert counts[PersonalityDimension.EI] == QUESTIONS_PER_DIMENSION
            assert counts[PersonalityDimension.SN] == QUESTIONS_PER_DIMENSION
            assert counts[PersonalityDimension.TF] == QUESTIONS_PER_DIMENSION
            assert counts[PersonalityDimension.JP] == QUESTIONS_PER_DIMENSION


def test_repeated_get_test_does_not_duplicate_session_links(client):
    token = start_session(client)
    for _ in range(5):
        assert client.get(f"/personality/test/{token}?q=0").status_code == 200
    with db_session(client) as db:
        session = session_by_token(db, token)
        count = db.scalar(
            select(func.count())
            .select_from(PersonalitySessionQuestion)
            .where(PersonalitySessionQuestion.session_id == session.id)
        )
        assert count == SESSION_QUESTION_COUNT
        ids = db.scalars(
            select(PersonalitySessionQuestion.question_id).where(
                PersonalitySessionQuestion.session_id == session.id
            )
        ).all()
        assert len(ids) == len(set(ids)) == SESSION_QUESTION_COUNT


def test_repeated_post_start_does_not_duplicate_session_links(client):
    client.get("/personality/instructions")
    token = start_session(client, "male")
    for gender in ("male", "female"):
        start = client.post("/personality/start", data={"gender": gender}, follow_redirects=False)
        assert start.status_code == 303
    with db_session(client) as db:
        session = session_by_token(db, token)
        count = db.scalar(
            select(func.count())
            .select_from(PersonalitySessionQuestion)
            .where(PersonalitySessionQuestion.session_id == session.id)
        )
        assert count == SESSION_QUESTION_COUNT


def test_database_rejects_duplicate_session_question_link(client):
    token = start_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        link = db.scalar(
            select(PersonalitySessionQuestion).where(
                PersonalitySessionQuestion.session_id == session.id
            )
        )
        assert link is not None
        db.add(
            PersonalitySessionQuestion(
                session_id=session.id,
                question_id=link.question_id,
                display_order=99,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

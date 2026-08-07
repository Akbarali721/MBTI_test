"""Ma'lumotlar qatlami: ball yo'nalishi, payment_code ustuni, seed va tozalash."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import event, func, select
from sqlalchemy.orm import Session as OrmSession

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityAnswer, PersonalityQuestion, PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import DIMENSION_POLES, seed_personality_questions
from tests.helpers import answer_question, db_session, extract_hidden, option_ids, start_session


def _answer_every_question(repo: PersonalityRepository, session, option_index: int) -> None:
    for question in repo.get_active_questions_ordered():
        options = sorted(question.options, key=lambda o: o.order_number)
        repo.upsert_answer(session.id, question.id, options[option_index].id)


def test_option_scores_follow_gradient_order(client):
    with db_session(client) as db:
        for question in PersonalityRepository(db).get_active_questions_ordered():
            left, right = DIMENSION_POLES[question.dimension]
            options = sorted(question.options, key=lambda o: o.order_number)
            assert [getattr(o, f"{left}_score") for o in options] == [1, 1, 0, 0]
            assert [getattr(o, f"{right}_score") for o in options] == [0, 0, 1, 1]


def test_opposite_pole_answers_give_opposite_type(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        first = repo.create_session(source="test")
        _answer_every_question(repo, first, 0)
        repo.recalculate_and_complete_session(first)

        last = repo.create_session(source="test")
        _answer_every_question(repo, last, 3)
        repo.recalculate_and_complete_session(last)
        db.commit()

        assert first.result_type == "ESTJ"
        assert last.result_type == "INFP"
        assert (first.e_score, first.i_score) == (6, 0)
        assert (last.e_score, last.i_score) == (0, 6)


def test_payment_code_stored_on_session_create(client):
    with db_session(client) as db:
        session = PersonalityRepository(db).create_session(source="test")
        db.commit()
        assert session.payment_code
        assert len(session.payment_code) >= 8
        assert session.token.startswith(session.payment_code)


def test_recompute_restores_scores_from_answers(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="test")
        _answer_every_question(repo, session, 3)
        repo.recalculate_and_complete_session(session)
        db.commit()

        session.e_score = 999
        session.result_type = "XXXX"
        db.commit()

        assert repo.recompute_stored_sessions() == 1
        db.commit()
        assert session.e_score == 0
        assert session.result_type == "INFP"


def test_force_seed_keeps_answers_and_ids(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        session = repo.create_session(source="test")
        _answer_every_question(repo, session, 0)
        db.commit()

        ids_before = sorted(db.scalars(select(PersonalityQuestion.id)).all())
        seed_personality_questions(db, force=True)
        ids_after = sorted(db.scalars(select(PersonalityQuestion.id)).all())
        answers = db.scalar(select(func.count()).select_from(PersonalityAnswer))

        assert ids_before == ids_after
        assert answers == 24


def test_purge_removes_only_stale_visited_sessions(client):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        stale = repo.create_session(source="test")
        stale.last_activity_at = datetime.now(timezone.utc) - timedelta(days=60)
        fresh = repo.create_session(source="test")
        started = repo.create_session(source="test")
        started.status = PersonalitySessionStatus.STARTED
        started.last_activity_at = datetime.now(timezone.utc) - timedelta(days=60)
        db.commit()

        removed = repo.delete_stale_visited_sessions(older_than_days=30)
        db.commit()

        assert removed == 1
        tokens = set(db.scalars(select(PersonalityTestSession.token)).all())
        assert fresh.token in tokens
        assert started.token in tokens


def test_answer_submit_commits_once(client):
    token = start_session(client)
    page = client.get(f"/personality/test/{token}?q=0")

    commits: list[int] = []

    def _count_commit(_session: OrmSession) -> None:
        commits.append(1)

    event.listen(OrmSession, "after_commit", _count_commit)
    try:
        answer = client.post(
            f"/personality/test/{token}/answer",
            data={
                "question_id": extract_hidden(page.text, "question_id"),
                "option_id": option_ids(page.text)[0],
                "question_index": "0",
            },
            follow_redirects=False,
        )
    finally:
        event.remove(OrmSession, "after_commit", _count_commit)

    assert answer.status_code == 303
    assert len(commits) == 1


def test_answers_are_upserted_not_appended(client):
    token = start_session(client)
    answer_question(client, token, 0, option_index=0)
    answer_question(client, token, 0, option_index=2)

    with db_session(client) as db:
        session = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert session is not None
        rows = list(db.scalars(select(PersonalityAnswer).where(PersonalityAnswer.session_id == session.id)))
    assert len(rows) == 1

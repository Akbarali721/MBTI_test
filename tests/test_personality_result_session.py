"""Natija kontenti, testni qayta boshlash va natija sahifasidagi harakatlar."""

from sqlalchemy import func, select

from app.i18n import t
from app.models.personality import PersonalityAnswer, PersonalityTestSession
from tests.helpers import (
    answer_question,
    complete_session,
    db_session,
    latest_session,
    session_by_token,
    start_session,
)


def test_completed_session_question_redirects_to_result(client):
    token = complete_session(client)
    resp = client.get(f"/personality/test/{token}?q=0", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == f"/personality/result/{token}"


def test_restart_creates_new_token_without_copying_answers(client):
    old_token = complete_session(client)
    with db_session(client) as db:
        old_id = session_by_token(db, old_token).id
        old_answers = db.scalar(
            select(func.count()).select_from(PersonalityAnswer).where(PersonalityAnswer.session_id == old_id)
        )
        total_questions = db.scalar(select(func.count()).select_from(PersonalityTestSession))
        assert total_questions == 1
    assert old_answers == 24

    restart = client.post("/personality/restart", follow_redirects=False)
    assert restart.status_code == 303
    assert restart.headers["location"] == "/personality/instructions"

    with db_session(client) as db:
        new_row = latest_session(db)
        assert new_row.token != old_token
        assert new_row.status.value in ("visited", "started", "in_progress")
        new_answers = db.scalar(
            select(func.count())
            .select_from(PersonalityAnswer)
            .where(PersonalityAnswer.session_id == new_row.id)
        )
        assert new_answers == 0
        assert session_by_token(db, old_token).status.value == "completed"


def test_result_page_has_actions_and_no_placeholder_word(client):
    token = complete_session(client)
    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200
    assert 'class="result-actions"' in result.text
    assert t("result.restart", "uz") in result.text
    assert t("common.back_home", "uz") in result.text
    assert 'href="/personality"' in result.text
    assert 'action="/personality/restart"' in result.text
    assert "placeholder" not in result.text.lower()


def test_home_route_works(client):
    assert client.get("/personality").status_code == 200


def test_root_redirects_to_personality(client):
    root = client.get("/", follow_redirects=False)
    assert root.status_code == 303
    assert root.headers["location"] == "/personality"


def test_in_progress_result_redirects_to_test(client):
    token = start_session(client)
    answer_question(client, token, 0)

    resp = client.get(f"/personality/result/{token}", follow_redirects=False)
    assert resp.status_code == 303
    assert f"/personality/test/{token}" in resp.headers["location"]


def test_back_link_lets_the_user_change_an_answer(client):
    token = start_session(client)
    answer_question(client, token, 0, option_index=0)
    first_page = client.get(f"/personality/test/{token}?q=0")
    assert "checked" in first_page.text

    answer_question(client, token, 0, option_index=3)
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        answers = db.scalar(
            select(func.count())
            .select_from(PersonalityAnswer)
            .where(PersonalityAnswer.session_id == session_id)
        )
    assert answers == 1, "javob qayta yozilishi kerak, yangi qator emas"

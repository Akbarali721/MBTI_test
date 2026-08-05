"""Result content, session restart, and result page actions."""

from sqlalchemy import func, select

from app.models.personality import PersonalityAnswer, PersonalityTestSession


def _complete_test_token(client, theme: str = "male") -> str:
    client.post("/personality/begin", follow_redirects=False)
    start = client.post(
        "/personality/start",
        data={"gender": theme},
        follow_redirects=False,
    )
    token = start.headers["location"].rstrip("/").split("/")[-1]
    for question_index in range(24):
        page = client.get(f"/personality/test/{token}?q={question_index}")
        question_id = _extract_hidden(page.text, "question_id")
        option_id = _first_option_id(page.text)
        client.post(
            f"/personality/test/{token}/answer",
            data={
                "question_id": question_id,
                "option_id": option_id,
                "question_index": str(question_index),
            },
            follow_redirects=False,
        )
    client.get(f"/personality/result/{token}/loading")
    return token


def _extract_hidden(html: str, name: str) -> int:
    marker = f'name="{name}" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return int(html[start:end])


def _first_option_id(html: str) -> int:
    import re

    match = re.search(r'name="option_id"\s+value="(\d+)"', html)
    if not match:
        match = re.search(r'value="(\d+)"\s+name="option_id"', html)
    assert match
    return int(match.group(1))


def test_completed_session_question_redirects_to_result(client):
    token = _complete_test_token(client)
    resp = client.get(f"/personality/test/{token}?q=0", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == f"/personality/result/{token}"


def test_restart_creates_new_token_without_copying_answers(client):
    old_token = _complete_test_token(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        old = db.scalar(
            select(PersonalityTestSession).where(PersonalityTestSession.token == old_token)
        )
        assert old is not None
        old_id = old.id
        old_answers = db.scalar(
            select(func.count()).select_from(PersonalityAnswer).where(
                PersonalityAnswer.session_id == old_id
            )
        )
        assert old_answers == 24
    finally:
        db.close()

    restart = client.post("/personality/restart", follow_redirects=False)
    assert restart.status_code == 303
    assert restart.headers["location"] == "/personality/instructions"

    db = factory()
    try:
        new_row = db.scalar(
            select(PersonalityTestSession)
            .order_by(PersonalityTestSession.id.desc())
            .limit(1)
        )
        assert new_row is not None
        assert new_row.token != old_token
        assert new_row.status.value in ("visited", "started", "in_progress")
        new_answers = db.scalar(
            select(func.count()).select_from(PersonalityAnswer).where(
                PersonalityAnswer.session_id == new_row.id
            )
        )
        assert new_answers == 0
        old_still = db.scalar(
            select(PersonalityTestSession).where(PersonalityTestSession.token == old_token)
        )
        assert old_still is not None
        assert old_still.status.value == "completed"
    finally:
        db.close()


def test_result_page_has_actions_and_no_placeholder_word(client):
    token = _complete_test_token(client)
    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200
    assert "Testni qayta ishlash" in result.text
    assert "Bosh sahifaga qaytish" in result.text
    assert 'href="/personality"' in result.text
    assert 'action="/personality/restart"' in result.text
    assert "placeholder" not in result.text.lower()


def test_home_route_works(client):
    assert client.get("/personality").status_code == 200


def test_in_progress_result_redirects_to_test(client):
    client.post("/personality/begin", follow_redirects=False)
    start = client.post("/personality/start", data={"gender": "male"}, follow_redirects=False)
    token = start.headers["location"].rstrip("/").split("/")[-1]
    page0 = client.get(f"/personality/test/{token}?q=0")
    client.post(
        f"/personality/test/{token}/answer",
        data={
            "question_id": _extract_hidden(page0.text, "question_id"),
            "option_id": _first_option_id(page0.text),
            "question_index": "0",
        },
        follow_redirects=False,
    )
    resp = client.get(f"/personality/result/{token}", follow_redirects=False)
    assert resp.status_code == 303
    assert f"/personality/test/{token}" in resp.headers["location"]

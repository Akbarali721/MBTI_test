import re

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.personality.payment_code import find_sessions_by_payment_code, payment_code_for_session


def _complete_session(client, theme: str = "male") -> str:
    client.get("/personality/instructions")
    post = client.post("/personality/start", data={"gender": theme}, follow_redirects=False)
    assert post.status_code == 303
    token = post.headers["location"].rstrip("/").split("/")[-1]
    for question_index in range(24):
        page = client.get(f"/personality/test/{token}?q={question_index}")
        qid = int(re.search(r'name="question_id" value="(\d+)"', page.text).group(1))
        oid = int(re.search(r'name="option_id"\s+value="(\d+)"', page.text).group(1))
        client.post(
            f"/personality/test/{token}/answer",
            data={"question_id": qid, "option_id": oid, "question_index": str(question_index)},
            follow_redirects=False,
        )
    client.get(f"/personality/result/{token}/loading")
    return token


def test_payment_code_for_completed_session(client):
    token = _complete_session(client)
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        from sqlalchemy import select

        from app.models.personality import PersonalityTestSession

        row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert row is not None
        code = payment_code_for_session(db, row)
        assert len(code) >= 8
        assert row.token.startswith(code)
        found = find_sessions_by_payment_code(db, code)
        assert len(found) == 1
        assert found[0].id == row.id
    finally:
        db.close()


def test_payment_code_expands_on_collision(client):
    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        from app.models.personality import PersonalityTestSession

        base = "0155ac4f"
        s1 = PersonalityTestSession(
            token=base + "a" * 24,
            status=PersonalitySessionStatus.COMPLETED,
        )
        s2 = PersonalityTestSession(
            token=base + "b" * 24,
            status=PersonalitySessionStatus.COMPLETED,
        )
        db.add_all([s1, s2])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        c1 = payment_code_for_session(db, s1)
        c2 = payment_code_for_session(db, s2)
        assert c1 != c2
        assert s1.token.startswith(c1)
        assert s2.token.startswith(c2)
    finally:
        db.close()


def test_result_support_bot_flow(client, monkeypatch):
    monkeypatch.setattr(settings, "payment_support_bot_username", "xarakter_test_support_bot")
    token = _complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert "Test kodi" in page.text
    assert 'target="_blank"' in page.text
    assert "rel=\"noopener noreferrer\"" in page.text

    redirect = client.get(f"/personality/result/{token}/support-bot", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == "https://t.me/xarakter_test_support_bot"


def test_support_bot_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "payment_support_bot_username", "")
    token = _complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert "To‘lov xizmati vaqtincha mavjud emas" in page.text

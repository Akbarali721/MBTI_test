from app.config import settings
from app.models.enums import PersonalitySessionStatus


def test_landing_creates_single_visitor_session_on_refresh(client):
    r1 = client.get("/personality?source=instagram")
    assert r1.status_code == 200
    r2 = client.get("/personality")
    assert r2.status_code == 200

    from sqlalchemy import func, select

    from app.models.personality import PersonalityTestSession

    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        count = db.scalar(select(func.count()).select_from(PersonalityTestSession))
        assert count == 1
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.status == PersonalitySessionStatus.VISITED
        assert row.source == "instagram"
    finally:
        db.close()


def test_admin_dashboard_and_sessions(client):
    client.get("/personality?source=direct")
    login = client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/admin"

    dash = client.get("/admin")
    assert dash.status_code == 200
    assert "Tashriflar" in dash.text
    assert "Tugatish foizi" in dash.text

    sessions = client.get("/admin/sessions")
    assert sessions.status_code == 200
    assert "visited" in sessions.text
    assert "direct" in sessions.text

    filtered = client.get("/admin/sessions?filter=visited")
    assert filtered.status_code == 200


def test_admin_session_detail_after_one_answer(client):
    client.get("/personality")
    client.get("/personality/instructions")
    post = client.post("/personality/start", data={"gender": "male"}, follow_redirects=False)
    assert post.status_code == 303
    token = post.headers["location"].rstrip("/").split("/")[-1]

    page = client.get(f"/personality/test/{token}?q=0")
    import re

    qid = int(re.search(r'name="question_id" value="(\d+)"', page.text).group(1))
    oid = int(re.search(r'name="option_id"\s+value="(\d+)"', page.text).group(1))
    client.post(
        f"/personality/test/{token}/answer",
        data={"question_id": qid, "option_id": oid, "question_index": "0"},
        follow_redirects=False,
    )

    client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    from sqlalchemy import select

    from app.models.personality import PersonalityTestSession

    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert row is not None
        assert row.status == PersonalitySessionStatus.STARTED
        assert row.answered_questions == 1
        sid = row.id
    finally:
        db.close()

    detail = client.get(f"/admin/sessions/{sid}")
    assert detail.status_code == 200
    assert "Berilgan javoblar" in detail.text
    assert "started" in detail.text

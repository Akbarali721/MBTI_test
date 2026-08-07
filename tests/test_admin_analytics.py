from sqlalchemy import func, select

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from tests.helpers import admin_login, answer_question, db_session, session_by_token, start_session


def test_landing_creates_single_visitor_session_on_refresh(client):
    assert client.get("/personality?source=instagram").status_code == 200
    assert client.get("/personality").status_code == 200

    with db_session(client) as db:
        assert db.scalar(select(func.count()).select_from(PersonalityTestSession)) == 1
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.status == PersonalitySessionStatus.VISITED
        assert row.source == "instagram"


def test_admin_dashboard_and_sessions(client):
    client.get("/personality?source=direct")
    login = admin_login(client)
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
    token = start_session(client)
    answer_question(client, token, 0)

    admin_login(client)
    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.status == PersonalitySessionStatus.STARTED
        assert row.answered_questions == 1
        session_id = row.id

    detail = client.get(f"/admin/sessions/{session_id}")
    assert detail.status_code == 200
    assert "Berilgan javoblar" in detail.text
    assert "started" in detail.text

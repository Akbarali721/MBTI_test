"""Natija fikri: API, upsert, admin."""

import json

from app.i18n import t
from app.models.personality import PersonalityResultUserFeedback
from app.services.result_user_feedback_service import ResultUserFeedbackService
from tests.helpers import complete_session, db_session, session_by_token


def test_user_feedback_submit_and_success_on_page(client):
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert t("feedback.user.title", "uz") in page.text

    resp = client.post(
        f"/personality/result/{token}/user-feedback",
        content=json.dumps({"rating": "positive", "comment": "Juda mos tushdi"}),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    with db_session(client) as db:
        session = session_by_token(db, token)
        row = db.query(PersonalityResultUserFeedback).filter_by(session_id=session.id).one()
        assert row.rating == "positive"
        assert row.comment == "Juda mos tushdi"

    again = client.get(f"/personality/result/{token}")
    assert t("feedback.user.success_title", "uz") in again.text
    assert t("feedback.user.title", "uz") not in again.text


def test_user_feedback_upsert_not_duplicate(client):
    token = complete_session(client)
    url = f"/personality/result/{token}/user-feedback"
    client.post(
        url,
        content=json.dumps({"rating": "partial", "comment": "Bir"}),
        headers={"Content-Type": "application/json"},
    )
    client.post(
        url,
        content=json.dumps({"rating": "negative", "comment": "Ikki"}),
        headers={"Content-Type": "application/json"},
    )
    with db_session(client) as db:
        session = session_by_token(db, token)
        rows = db.query(PersonalityResultUserFeedback).filter_by(session_id=session.id).all()
        assert len(rows) == 1
        assert rows[0].rating == "negative"
        assert rows[0].comment == "Ikki"


def test_admin_feedback_page(client):
    token = complete_session(client)
    client.post(
        f"/personality/result/{token}/user-feedback",
        content=json.dumps({"rating": "positive"}),
        headers={"Content-Type": "application/json"},
    )
    login = client.post(
        "/admin/login",
        data={"username": "test-admin", "password": "test-admin-parol-2026"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    page = client.get("/admin/feedback")
    assert page.status_code == 200
    assert "Jami feedback" in page.text
    assert "👍" in page.text

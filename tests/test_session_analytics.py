"""Session analytics: intent, source, feedback, admin ko'rinishi."""

from sqlalchemy import func, select

from app.i18n import t
from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.personality.analytics_constants import DEFAULT_SOURCE
from tests.helpers import (
    admin_login,
    answer_question,
    complete_session,
    db_session,
    session_by_token,
    start_session,
)


def test_landing_source_defaults_to_direct_without_query(client):
    client.get("/personality")
    with db_session(client) as db:
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.source == DEFAULT_SOURCE


def test_source_query_overrides_direct_on_landing(client):
    client.get("/personality?source=ig_strength_01")
    with db_session(client) as db:
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.source == "ig_strength_01"


def test_source_persists_via_instructions_query(client):
    client.get("/personality/instructions?source=ig_career_01")
    with db_session(client) as db:
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.source == "ig_career_01"


def test_intent_saved_once_and_skipped_on_return(client):
    token = start_session(client, intent="strengths")
    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.intent == "strengths"

    intent_page = client.get("/personality/intent", follow_redirects=False)
    assert intent_page.status_code == 303
    assert f"/personality/test/{token}" in intent_page.headers["location"]


def test_test_started_at_set_on_first_question_page(client):
    client.get("/personality/instructions")
    start = client.post("/personality/start", data={"gender": "male"}, follow_redirects=False)
    assert start.headers["location"] == "/personality/intent"
    intent = client.post("/personality/intent", data={"intent": "curiosity"}, follow_redirects=False)
    token = intent.headers["location"].split("/test/")[1].split("?")[0]
    with db_session(client) as db:
        before = session_by_token(db, token)
        assert before.started_at is None

    page = client.get(f"/personality/test/{token}?q=0")
    assert page.status_code == 200
    with db_session(client) as db:
        after = session_by_token(db, token)
        assert after.started_at is not None


def test_feedback_rating_and_interest_saved(client):
    token = complete_session(client, open_result=False)
    result = client.get(f"/personality/result/{token}")
    assert t("feedback.rating.title", "uz") in result.text

    rated = client.post(
        f"/personality/result/{token}/feedback",
        data={"rating": "very_accurate"},
        follow_redirects=False,
    )
    assert rated.status_code == 303
    after_rating = client.get(f"/personality/result/{token}")
    assert t("feedback.interest.title", "uz") in after_rating.text

    interested = client.post(
        f"/personality/result/{token}/feedback",
        data={"interest": "career"},
        follow_redirects=False,
    )
    assert interested.status_code == 303

    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.feedback_rating == "very_accurate"
        assert row.feedback_interest == "career"

    final = client.get(f"/personality/result/{token}")
    assert t("feedback.rating.title", "uz") not in final.text


def test_feedback_skip_hides_block(client):
    token = complete_session(client, open_result=False)
    skipped = client.post(
        f"/personality/result/{token}/feedback",
        data={"skip": "1"},
        follow_redirects=False,
    )
    assert skipped.status_code == 303
    result = client.get(f"/personality/result/{token}")
    assert t("feedback.rating.title", "uz") not in result.text


def test_admin_sessions_show_intent_and_summary(client):
    client.get("/personality?source=tg_post_01")
    token = start_session(client, intent="career")
    question_index = 0
    while True:
        location = answer_question(client, token, question_index)
        if location.endswith("/loading"):
            break
        question_index += 1
    assert client.get(f"/personality/result/{token}/loading").status_code == 200

    admin_login(client)
    page = client.get("/admin/sessions")
    assert page.status_code == 200
    assert "Jami kirganlar" in page.text
    assert "Test boshlaganlar" in page.text
    assert "Kasb/yo‘nalish" in page.text
    assert "tg_post_01" in page.text


def test_completed_at_set_after_full_test(client):
    token = complete_session(client, open_result=False)
    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.status == PersonalitySessionStatus.COMPLETED
        assert row.completed_at is not None

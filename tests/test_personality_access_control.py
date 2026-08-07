"""Egalik tekshiruvi, tugallangan natijani saqlash va imzolangan natija havolasi."""

from sqlalchemy import func, select

from app.models.personality import PersonalityTestSession
from app.personality.session_binding import make_result_access_token, verify_result_access_token
from tests.helpers import (
    complete_session,
    db_session,
    extract_hidden,
    first_option_id,
    start_session,
)


def test_foreign_token_cannot_open_question_page(client):
    token_a = start_session(client)
    page = client.get(f"/personality/test/{token_a}?q=0")
    question_id = extract_hidden(page.text, "question_id")
    option_id = first_option_id(page.text)

    client.cookies.clear()
    start_session(client)

    denied = client.get(f"/personality/test/{token_a}?q=0", follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers["location"] == "/personality"

    denied_answer = client.post(
        f"/personality/test/{token_a}/answer",
        data={"question_id": question_id, "option_id": option_id, "question_index": "0"},
        follow_redirects=False,
    )
    assert denied_answer.status_code == 303
    assert denied_answer.headers["location"] == "/personality"


def test_landing_visit_keeps_completed_result_reachable(client):
    token = complete_session(client)
    assert client.get("/personality").status_code == 200
    assert client.get(f"/personality/result/{token}", follow_redirects=False).status_code == 200


def test_restart_keeps_previous_result_reachable(client):
    token = complete_session(client)
    restart = client.post("/personality/restart", follow_redirects=False)
    assert restart.status_code == 303
    assert client.get(f"/personality/result/{token}", follow_redirects=False).status_code == 200


def test_signed_access_link_opens_result_on_another_device(client):
    token = complete_session(client)
    signed = make_result_access_token(token)

    client.cookies.clear()
    assert client.get(f"/personality/result/{token}", follow_redirects=False).status_code == 303

    allowed = client.get(f"/personality/result/{token}?access={signed}", follow_redirects=False)
    assert allowed.status_code == 200
    # Imzo bir marta tekshirilgach sahifa qayta yuklanishi ham ishlaydi.
    assert client.get(f"/personality/result/{token}", follow_redirects=False).status_code == 200


def test_invalid_signed_access_is_rejected(client):
    token = complete_session(client)
    signed = make_result_access_token(token)

    client.cookies.clear()
    denied = client.get(f"/personality/result/{token}?access=not-a-signature", follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers["location"] == "/personality"

    assert verify_result_access_token(token, signed) is True
    assert verify_result_access_token(token + "x", signed) is False
    assert verify_result_access_token(token, signed + "x") is False
    assert verify_result_access_token(token, "") is False
    assert verify_result_access_token("", signed) is False


def _session_count(client) -> int:
    with db_session(client) as db:
        return int(db.scalar(select(func.count()).select_from(PersonalityTestSession)) or 0)


def test_crawler_and_prefetch_landing_hits_create_no_rows(client):
    crawler = client.get(
        "/personality",
        headers={"user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
    )
    assert crawler.status_code == 200
    prefetch = client.get("/personality", headers={"sec-purpose": "prefetch;prerender"})
    assert prefetch.status_code == 200
    assert _session_count(client) == 0

    human = client.get("/personality")
    assert human.status_code == 200
    assert _session_count(client) == 1


def test_telegram_user_id_query_must_be_int(client):
    bad = client.get("/personality/appearance?telegram_user_id=abc", follow_redirects=False)
    assert bad.status_code == 422
    good = client.get("/personality/appearance?telegram_user_id=42", follow_redirects=False)
    assert good.status_code == 303


def test_support_bot_endpoints_require_ownership(client):
    token = complete_session(client)
    client.cookies.clear()
    start_session(client)

    for method, path in (
        ("GET", f"/personality/result/{token}/support-bot"),
        ("POST", f"/personality/result/{token}/support-bot"),
        ("POST", f"/personality/result/{token}/request-premium"),
    ):
        denied = client.request(method, path, follow_redirects=False)
        assert denied.status_code == 303, (method, path)
        assert denied.headers["location"] == "/personality", (method, path)

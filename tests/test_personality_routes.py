"""Veb oqimi: landing → koʻrsatma → savollar → natija → premium.

Assertionlar barqaror belgilarga (id / class / marshrut) va i18n katalogiga tayanadi,
qattiq yozilgan marketing jumlalariga emas.
"""

from app.i18n import t
from app.models.enums import AppearanceTheme
from app.personality.session_binding import make_result_access_token
from app.personality.themes import has_appearance_choice, resolve_theme_key
from tests.helpers import (
    admin_login,
    answer_question,
    complete_session,
    db_session,
    latest_session,
    session_by_token,
    session_id_for_token,
    start_session,
)

BRAND_LOGO_MARKER = 'class="personality-brand'
LOCKED_PREMIUM_MARKER = "mbti-premium-locked-note"


def test_personality_full_flow_and_premium_grant(client):
    landing = client.get("/personality")
    assert landing.status_code == 200
    assert 'id="landing-title"' in landing.text
    assert t("landing.headline", "uz") in landing.text
    assert 'action="/personality/begin"' in landing.text
    # Landingʼda brend logotipi yoʻq — faqat qahramon rasm.
    assert BRAND_LOGO_MARKER not in landing.text
    assert "personality-hero-image" in landing.text
    assert "images/personality/personality-hero.webp" in landing.text

    token = start_session(client, "male")

    question_index = 0
    while True:
        page = client.get(f"/personality/test/{token}?q={question_index}")
        assert page.status_code == 200
        assert "theme-male" in page.text
        location = answer_question(client, token, question_index)
        if location.endswith("/loading"):
            break
        assert f"q={question_index + 1}" in location
        question_index += 1

    loading = client.get(f"/personality/result/{token}/loading")
    assert loading.status_code == 200
    assert "theme-male" in loading.text

    result = client.get(f"/personality/result/{token}")
    assert result.status_code == 200
    assert t("result.eyebrow_after", "uz").strip() in result.text
    assert result.text.count(BRAND_LOGO_MARKER) == 1
    assert LOCKED_PREMIUM_MARKER in result.text

    skip_appearance = client.get("/personality/appearance", follow_redirects=False)
    assert skip_appearance.status_code == 303
    assert skip_appearance.headers["location"] == "/personality/instructions"

    req = client.post(f"/personality/result/{token}/request-premium", follow_redirects=False)
    assert req.status_code == 303

    # Admin login session fixationʼga qarshi sessiyani tozalaydi, shuning uchun
    # tashrifchi cookieʼsi alohida saqlanadi (real hayotda bu boshqa brauzer boʻladi).
    visitor_cookie = client.cookies.get("session")
    admin_login(client)

    grant = client.post(
        f"/admin/personality/{session_id_for_token(client, token)}/grant-premium",
        follow_redirects=False,
    )
    assert grant.status_code == 303

    client.cookies.set("session", visitor_cookie)

    # Cookie tiklansa ham admin login sessiyani tozalagan boʻlishi mumkin, shuning uchun
    # natija imzolangan havola bilan ochiladi (bot tasdiqlagach shu havolani yuboradi).
    result_premium = client.get(
        f"/personality/result/{token}?access={make_result_access_token(token)}",
        follow_redirects=False,
    )
    assert result_premium.status_code == 200
    assert LOCKED_PREMIUM_MARKER not in result_premium.text
    assert "placeholder" not in result_premium.text.lower()
    assert t("result.section.motivation", "uz") in result_premium.text

    retest = client.get(f"/personality/test/{token}", follow_redirects=False)
    assert retest.status_code == 303
    assert retest.headers["location"] == f"/personality/result/{token}"


def test_all_gender_themes_save_and_apply(client):
    for theme, css_class in [("male", "theme-male"), ("female", "theme-female")]:
        client.cookies.clear()
        token = start_session(client, theme)

        page = client.get(f"/personality/test/{token}?q=0")
        assert page.status_code == 200
        assert css_class in page.text
        assert page.text.count(BRAND_LOGO_MARKER) == 1
        assert "personality-hero-image" not in page.text


def test_start_without_gender_shows_error(client):
    client.get("/personality/instructions")
    post = client.post("/personality/start", data={}, follow_redirects=False)
    assert post.status_code == 400
    assert 'class="ref-alert"' in post.text
    assert "jinsingizni tanlang" in post.text


def test_invalid_gender_rejected_on_start(client):
    client.get("/personality/instructions")
    post = client.post("/personality/start", data={"gender": "neutral"}, follow_redirects=False)
    assert post.status_code == 400
    assert 'class="ref-alert"' in post.text


def test_old_session_without_appearance_redirects_to_instructions(client):
    client.get("/personality/instructions")

    with db_session(client) as db:
        row = latest_session(db)
        token = row.token
        assert row.appearance_theme is None
        assert has_appearance_choice(row) is False
        assert resolve_theme_key(row) == AppearanceTheme.MALE.value

    test_page = client.get(f"/personality/test/{token}?q=0", follow_redirects=False)
    assert test_page.status_code == 303
    assert test_page.headers["location"] == "/personality/instructions"


def test_instructions_shows_single_logo(client):
    page = client.get("/personality/instructions")
    assert page.status_code == 200
    assert page.text.count(BRAND_LOGO_MARKER) == 1
    assert t("instructions.title", "uz") in page.text
    assert "gender-selector" in page.text


def test_relationship_route_still_available(client):
    response = client.get("/relationship")
    assert response.status_code == 200
    assert t("compat.title", "uz") in response.text


def test_completed_session_is_readable_from_the_database(client):
    token = complete_session(client)
    with db_session(client) as db:
        row = session_by_token(db, token)
        assert row.status.value == "completed"
        assert row.result_type

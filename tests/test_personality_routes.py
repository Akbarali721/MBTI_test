import re



from app.config import settings

from app.models.enums import AppearanceTheme

from app.personality.themes import has_appearance_choice, resolve_theme_key





def _go_through_instructions(client, theme: str) -> str:

    instructions = client.get("/personality/instructions")

    assert instructions.status_code == 200

    assert "gender-selector" in instructions.text

    post = client.post(

        "/personality/start",

        data={"gender": theme},

        follow_redirects=False,

    )

    assert post.status_code == 303

    test_url = post.headers["location"]

    return test_url.rstrip("/").split("/")[-1]





def test_personality_full_flow_and_premium_grant(client):

    landing = client.get("/personality")

    assert landing.status_code == 200

    assert "Siz dangasa emassiz" in landing.text

    assert 'action="/personality/begin"' in landing.text

    assert landing.text.count("personality-logo.png") == 0

    assert "personality-hero-image" in landing.text

    assert "images/personality/personality-hero.png" in landing.text



    token = _go_through_instructions(client, "male")



    for question_index in range(24):

        page = client.get(f"/personality/test/{token}?q={question_index}")

        assert page.status_code == 200

        assert "theme-male" in page.text

        question_id = _extract_hidden(page.text, "question_id")

        option_id = _first_option_id(page.text)

        answer = client.post(

            f"/personality/test/{token}/answer",

            data={

                "question_id": question_id,

                "option_id": option_id,

                "question_index": str(question_index),

            },

            follow_redirects=False,

        )

        if question_index < 23:

            assert answer.status_code == 303

            assert f"q={question_index + 1}" in answer.headers["location"]

        else:

            assert answer.status_code == 303

            assert answer.headers["location"].endswith("/loading")



    loading = client.get(f"/personality/result/{token}/loading")

    assert loading.status_code == 200

    assert "theme-male" in loading.text



    result = client.get(f"/personality/result/{token}")

    assert result.status_code == 200

    assert "tipiga eng yaqin" in result.text

    assert result.text.count("personality-logo.png") == 1



    skip_appearance = client.get("/personality/appearance", follow_redirects=False)

    assert skip_appearance.status_code == 303

    assert skip_appearance.headers["location"] == "/personality/instructions"



    req = client.post(f"/personality/result/{token}/request-premium", follow_redirects=False)

    assert req.status_code == 303



    login = client.post(

        "/admin/login",

        data={"username": settings.admin_username, "password": settings.admin_password},

        follow_redirects=False,

    )

    assert login.status_code == 303



    grant = client.post(
        f"/admin/personality/{_session_id_for_token(client, token)}/grant-premium",
        follow_redirects=False,
    )

    assert grant.status_code == 303



    result_premium = client.get(f"/personality/result/{token}")

    assert "Premium tahlil — ochish uchun" not in result_premium.text

    assert "placeholder" not in result_premium.text.lower()
    assert "Motivatsiyangiz" in result_premium.text or "motivatsiyangiz" in result_premium.text.lower()



    retest = client.get(f"/personality/test/{token}", follow_redirects=False)

    assert retest.status_code == 303

    assert retest.headers["location"] == f"/personality/result/{token}"





def test_all_gender_themes_save_and_apply(client):

    for theme, css_class in [

        ("male", "theme-male"),

        ("female", "theme-female"),

    ]:

        client.cookies.clear()

        token = _go_through_instructions(client, theme)

        page = client.get(f"/personality/test/{token}?q=0")

        assert page.status_code == 200

        assert css_class in page.text

        assert page.text.count("personality-logo.png") == 1

        assert "personality-hero" not in page.text





def test_start_without_gender_shows_error(client):

    client.get("/personality/instructions")

    post = client.post("/personality/start", data={}, follow_redirects=False)

    assert post.status_code == 400

    assert "Davom etish uchun jinsingizni tanlang" in post.text





def test_invalid_gender_rejected_on_start(client):

    client.get("/personality/instructions")

    post = client.post("/personality/start", data={"gender": "neutral"}, follow_redirects=False)

    assert post.status_code == 400

    assert "Davom etish uchun jinsingizni tanlang" in post.text





def test_old_session_without_appearance_redirects_to_instructions(client):

    client.get("/personality/instructions")

    token = _latest_session_token(client)



    from sqlalchemy import select



    from app.models.personality import PersonalityTestSession



    factory = client.testing_session_factory  # type: ignore[attr-defined]

    db = factory()

    try:

        row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))

        assert row is not None

        assert row.appearance_theme is None

        assert has_appearance_choice(row) is False

        assert resolve_theme_key(row) == AppearanceTheme.MALE.value

    finally:

        db.close()



    test_page = client.get(f"/personality/test/{token}?q=0", follow_redirects=False)

    assert test_page.status_code == 303

    assert test_page.headers["location"] == "/personality/instructions"





def test_instructions_shows_single_logo(client):

    page = client.get("/personality/instructions")

    assert page.status_code == 200

    assert page.text.count("personality-logo.png") == 1

    assert "Testdan oldin" in page.text





def test_relationship_route_still_available(client):

    response = client.get("/relationship")

    assert response.status_code == 200

    assert "Munosabat testi" in response.text





def _latest_session_token(client) -> str:

    from sqlalchemy import select



    from app.models.personality import PersonalityTestSession



    factory = client.testing_session_factory  # type: ignore[attr-defined]

    db = factory()

    try:

        row = db.scalar(

            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)

        )

        assert row is not None

        return row.token

    finally:

        db.close()





def _extract_hidden(html: str, name: str) -> int:

    marker = f'name="{name}" value="'

    start = html.index(marker) + len(marker)

    end = html.index('"', start)

    return int(html[start:end])





def _first_option_id(html: str) -> int:

    match = re.search(r'name="option_id"\s+value="(\d+)"', html)

    if not match:

        match = re.search(r'value="(\d+)"\s+name="option_id"', html)

    assert match, "option_id input not found"

    return int(match.group(1))





def _session_id_for_token(client, token: str) -> int:
    from sqlalchemy import select

    from app.models.personality import PersonalityTestSession

    factory = client.testing_session_factory  # type: ignore[attr-defined]
    db = factory()
    try:
        row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
        assert row is not None
        return row.id
    finally:
        db.close()


def _session_id(client) -> int:

    admin_page = client.get("/admin/personality/sessions")

    match = re.search(r"<td>(\d+)</td>", admin_page.text)

    assert match

    return int(match.group(1))


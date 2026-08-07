"""Til qatlami: ?lang=, cookie, Accept-Language va natija kontenti tili."""

from app.i18n import DEFAULT, LANG_COOKIE_KEY, normalize_lang, resolve_lang, t
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import seed_personality_results
from tests.helpers import complete_session, db_session, session_by_token


def test_normalize_lang_accepts_region_codes_and_rejects_the_rest():
    assert normalize_lang("ru") == "ru"
    assert normalize_lang("RU-ru") == "ru"
    assert normalize_lang("uz_UZ") == "uz"
    assert normalize_lang("xx") is None
    assert normalize_lang("") is None
    assert normalize_lang(None) is None


def test_translation_falls_back_to_the_default_catalog():
    assert t("landing.cta", "de") == t("landing.cta", DEFAULT)
    assert t("bunday.kalit.yoq", "uz") == "bunday.kalit.yoq"
    # Notoʻgʻri joker sahifani yiqitmaydi.
    assert t("question.title", "uz", current=3) == t("question.title", "uz")


def test_query_switches_the_interface_to_russian(client):
    page = client.get("/personality?lang=ru")
    assert page.status_code == 200
    assert 'lang="ru"' in page.text
    assert t("landing.headline", "ru") in page.text
    assert t("landing.headline", "uz") not in page.text
    assert client.cookies.get(LANG_COOKIE_KEY) == "ru"


def test_language_choice_is_remembered_in_a_cookie(client):
    client.get("/personality?lang=ru")

    instructions = client.get("/personality/instructions")
    assert 'lang="ru"' in instructions.text
    assert t("instructions.start", "ru") in instructions.text


def test_unknown_language_falls_back_to_uzbek_without_a_cookie(client):
    page = client.get("/personality?lang=xx")
    assert 'lang="uz"' in page.text
    assert t("landing.headline", "uz") in page.text
    assert client.cookies.get(LANG_COOKIE_KEY) is None


def test_cookie_can_be_overridden_by_a_new_query(client):
    client.get("/personality?lang=ru")
    back = client.get("/personality?lang=uz")
    assert 'lang="uz"' in back.text
    assert client.cookies.get(LANG_COOKIE_KEY) == "uz"


def test_accept_language_header_is_used_when_nothing_was_chosen(client):
    page = client.get("/personality", headers={"accept-language": "en;q=0.8, ru-RU;q=0.9"})
    assert 'lang="ru"' in page.text


def test_language_switcher_keeps_the_current_path_and_query(client):
    page = client.get("/personality?source=telegram")
    assert 'href="/personality?source=telegram&amp;lang=ru"' in page.text


def test_result_content_falls_back_to_uzbek_when_translation_is_missing(client):
    """Fixture faqat "uz" kontentini yuklaydi: interfeys ruscha, matn oʻzbekcha qoladi."""
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}?lang=ru")

    assert page.status_code == 200
    assert t("result.strengths", "ru") in page.text
    with db_session(client) as db:
        uz_content = PersonalityRepository(db).get_result_content(session_by_token(db, token).result_type)
        assert uz_content is not None
        uz_title = uz_content.title
    assert uz_title in page.text


def test_russian_result_content_is_used_when_it_is_seeded(client):
    token = complete_session(client)
    with db_session(client) as db:
        seed_personality_results(db, language="ru")
        result_type = session_by_token(db, token).result_type
        repo = PersonalityRepository(db)
        ru_title = repo.get_result_content(result_type, "ru").title
        uz_title = repo.get_result_content(result_type, "uz").title
    assert ru_title != uz_title

    page = client.get(f"/personality/result/{token}?lang=ru")
    assert ru_title in page.text
    assert uz_title not in page.text

    uz_page = client.get(f"/personality/result/{token}?lang=uz")
    assert uz_title in uz_page.text


def test_resolve_lang_prefers_query_over_cookie_over_header():
    from starlette.requests import Request

    def _request(query: str, cookie: str | None, header: str | None) -> Request:
        headers = []
        if cookie:
            headers.append((b"cookie", f"{LANG_COOKIE_KEY}={cookie}".encode()))
        if header:
            headers.append((b"accept-language", header.encode()))
        return Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/personality",
                "query_string": query.encode(),
                "headers": headers,
            }
        )

    assert resolve_lang(_request("lang=ru", "uz", "uz")) == "ru"
    assert resolve_lang(_request("", "ru", "uz")) == "ru"
    assert resolve_lang(_request("", None, "ru-RU,ru;q=0.9")) == "ru"
    assert resolve_lang(_request("lang=xx", None, None)) == DEFAULT

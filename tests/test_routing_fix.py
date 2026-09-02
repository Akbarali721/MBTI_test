"""Routing: WebApp URL, legacy redirects, 404 til."""

from __future__ import annotations

from app.config import Settings


def _settings(**overrides) -> Settings:
    base = {
        "debug": True,
        "secret_key": "test-secret-key-not-a-placeholder",
        "admin_password_hash": "x",
    }
    base.update(overrides)
    return Settings(**base)


def test_web_app_url_avoids_double_personality():
    s = _settings(public_base_url="https://example.com/personality")
    assert s.effective_web_app_url == "https://example.com/personality"


def test_web_app_url_defaults_to_site_root():
    s = _settings(public_base_url="https://example.com")
    assert s.effective_web_app_url == "https://example.com"


def test_web_app_url_strips_wrong_start_suffix():
    s = _settings(web_app_url="https://example.com/start")
    assert s.effective_web_app_url == "https://example.com"


def test_web_app_url_strips_personality_then_start():
    s = _settings(web_app_url="https://example.com/personality/start")
    assert s.effective_web_app_url == "https://example.com/personality"


def test_web_app_url_debug_shows_source():
    s = _settings(
        public_base_url="https://mbtitest-production.up.railway.app",
        web_app_url="",
    )
    info = s.web_app_url_debug()
    assert info["source"] == "PUBLIC_BASE_URL"
    assert info["final"] == "https://mbtitest-production.up.railway.app"


def test_legacy_start_redirects_to_root(client):
    response = client.get("/start", headers={"accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_root_redirects_to_personality(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/personality"


def test_lang_legacy_paths(client):
    uz = client.get("/uz", follow_redirects=False)
    assert uz.status_code == 303
    assert uz.headers["location"] == "/?lang=uz"

    ru = client.get("/ru", follow_redirects=False)
    assert ru.status_code == 303
    assert ru.headers["location"] == "/?lang=ru"


def test_get_personality_start_redirects(client):
    response = client.get("/personality/start", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/personality/instructions"


def test_404_page_is_consistent_uzbek_with_lang_cookie(client):
    response = client.get(
        "/bunday-sahifa-yoq",
        headers={"accept": "text/html", "accept-language": "ru-RU,ru;q=0.9"},
        cookies={"lang": "uz"},
    )
    assert response.status_code == 404
    assert "Sahifa topilmadi" in response.text
    assert "Bosh sahifaga qaytish" in response.text
    assert "Вернуться на главную" not in response.text
    assert "Проверьте адрес" not in response.text


def test_404_page_is_consistent_russian_with_lang_cookie(client):
    response = client.get(
        "/bunday-sahifa-yoq",
        headers={"accept": "text/html", "accept-language": "uz-UZ,uz;q=0.9"},
        cookies={"lang": "ru"},
    )
    assert response.status_code == 404
    assert "Страница не найдена" in response.text
    assert "Вернуться на главную" in response.text
    assert "Sahifa topilmadi" not in response.text

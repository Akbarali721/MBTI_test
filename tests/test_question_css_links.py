import re

from app.paths import STATIC_DIR
from tests.helpers import start_session

# Kesh-buster qiymati asset_url() tomonidan fayl mazmunidan hosil qilinadi,
# shuning uchun testlar aniq versiyaga emas, faqat uning borligiga tayanadi.
_CACHE_BUSTED = r"\?v=[0-9a-f]+"


def _question_html(client, gender: str = "male") -> str:
    token = start_session(client, gender)
    page = client.get(f"/personality/test/{token}?q=0")
    assert page.status_code == 200
    return page.text


def test_question_page_includes_stylesheet_links(client):
    html = _question_html(client)
    assert re.search(r"/static/css/personality\.css" + _CACHE_BUSTED, html)
    assert re.search(r"/static/css/personality-marketing\.css" + _CACHE_BUSTED, html)
    assert "mbti-option" in html
    assert "next-question-button" in html
    assert "choice-form.js" in html


def test_question_page_theme_female_in_html(client):
    html = _question_html(client, gender="female")
    assert "ref-page ref-page--flow theme-female" in html
    assert "theme-male" not in html


def test_question_page_theme_male_in_html(client):
    html = _question_html(client, gender="male")
    assert "theme-male" in html
    assert "ref-page ref-page--flow theme-male" in html


def test_personality_marketing_css_served_with_mbti_option(client):
    html = _question_html(client)
    hrefs = re.findall(r'<link[^>]+href="([^"]+)"', html)
    css_hrefs = [h for h in hrefs if "personality" in h and ".css" in h]
    assert len(css_hrefs) >= 2

    marketing_href = next(h for h in css_hrefs if "personality-marketing.css" in h)
    assert re.search(_CACHE_BUSTED + r"$", marketing_href)
    path = marketing_href.split("?", 1)[0]
    if not path.startswith("/"):
        path = marketing_href.replace("http://testserver", "").split("?", 1)[0]
    resp = client.get(path)
    assert resp.status_code == 200
    assert ".ref-page.theme-female" in resp.text
    assert ".mbti-option" in resp.text


def test_marketing_css_loaded_once_per_page(client):
    """Bir xil CSS ikki marta yuklanmasin (avval result.html uni takrorlagan)."""
    html = _question_html(client)
    assert html.count("/static/css/personality-marketing.css") == 1


def test_static_dir_points_at_app_static():
    assert (STATIC_DIR / "css" / "personality-marketing.css").is_file()

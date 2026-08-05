import re

from app.paths import STATIC_DIR


def _question_html(client, gender: str = "male") -> str:
    client.get("/personality/instructions")
    start = client.post(
        "/personality/start",
        data={"gender": gender},
        follow_redirects=False,
    )
    assert start.status_code == 303
    token = start.headers["location"].rstrip("/").split("/")[-1]
    page = client.get(f"/personality/test/{token}?q=0")
    assert page.status_code == 200
    return page.text


def test_question_page_includes_stylesheet_links(client):
    html = _question_html(client)
    assert "personality.css?v=12" in html
    assert "personality-marketing.css?v=20" in html
    assert "mbti-option" in html
    assert "next-question-button" in html
    assert "question-form.js" in html


def test_question_page_theme_female_in_html(client):
    html = _question_html(client, gender="female")
    assert 'class="personality-body ref-page ref-page--flow theme-female"' in html.replace(
        "  ", " "
    ) or "theme-female" in html
    assert "ref-page ref-page--flow theme-female" in html


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
    assert "?v=20" in marketing_href
    path = marketing_href.split("?", 1)[0]
    if not path.startswith("/"):
        path = marketing_href.replace("http://testserver", "").split("?", 1)[0]
    resp = client.get(path)
    assert resp.status_code == 200
    assert ".ref-page.theme-female" in resp.text
    assert ".mbti-option" in resp.text


def test_static_dir_points_at_app_static():
    assert (STATIC_DIR / "css" / "personality-marketing.css").is_file()

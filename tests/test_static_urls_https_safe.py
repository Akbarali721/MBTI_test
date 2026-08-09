import re


def test_static_asset_urls_are_relative_not_http(client):
    page = client.get("/personality")
    assert page.status_code == 200
    hrefs = re.findall(r'<link[^>]+href="([^"]+)"', page.text)
    css_hrefs = [h for h in hrefs if "personality" in h and ".css" in h]
    assert len(css_hrefs) >= 2
    for href in css_hrefs:
        assert not href.startswith("http://"), href
        assert not href.startswith("https://127.0.0.1"), href
        assert href.startswith("/static/"), href

    js_hrefs = re.findall(r'<script[^>]+src="([^"]+)"', page.text)
    for href in js_hrefs:
        if "/static/" in href:
            assert not href.startswith("http://"), href

    img_hrefs = re.findall(r'<img[^>]+src="([^"]+)"', page.text)
    for href in img_hrefs:
        if "/static/" in href or "personality" in href:
            assert not href.startswith("http://"), href

"""O'sish kanallari: ommaviy ulashish sahifasi va test tarixi."""

import re

from fastapi.testclient import TestClient

from app.main import app
from app.personality.share_code import generate_share_code, share_path, telegram_share_url
from tests.helpers import complete_session, db_session, session_by_token

SHARE_URL_RE = re.compile(r"https?://[^\s\"<]+/r/([A-Za-z0-9_-]+)")


def _share_code(client, token: str) -> str:
    with db_session(client) as db:
        code = session_by_token(db, token).share_code
    assert code, "sessiyada share_code yo'q"
    return code


# --------------------------- ulashish kodi ---------------------------


def test_share_code_is_created_and_differs_from_payment_code(client):
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.share_code
        assert session.share_code != session.payment_code
        # Ulashish kodi tokendan hosil qilinmasligi kerak — aks holda u tokenni oshkor qiladi.
        assert session.share_code not in session.token


def test_generate_share_code_is_unique_per_call(client):
    with db_session(client) as db:
        codes = {generate_share_code(db) for _ in range(20)}
    assert len(codes) == 20


# --------------------------- ommaviy sahifa ---------------------------


def test_shared_result_is_public_without_cookie(client):
    token = complete_session(client)
    code = _share_code(client, token)

    # Cookie'siz mutlaqo yangi mijoz — ulashilgan havolani ochadigan begona odam.
    with TestClient(app) as stranger:
        response = stranger.get(share_path(code))

    assert response.status_code == 200
    with db_session(client) as db:
        result_type = session_by_token(db, token).result_type
    assert result_type in response.text


def test_shared_result_hides_premium_and_personal_data(client):
    token = complete_session(client)
    code = _share_code(client, token)

    with TestClient(app) as stranger:
        html = stranger.get(share_path(code)).text

    # Sessiya tokeni va to'lov kodi ommaviy sahifaga hech qachon chiqmasligi kerak.
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.token not in html
        assert session.payment_code not in html
    # To'lov oqimi elementlari ham yo'q.
    for marker in ("payment-modal", "premium-card", "so‘m"):
        assert marker not in html


def test_shared_result_404_for_unknown_code(client):
    assert client.get(share_path("yoq-bunday-kod")).status_code == 404


def test_shared_result_404_before_completion(client):
    client.get("/personality")
    client.get("/personality/instructions")
    start = client.post("/personality/start", data={"gender": "male"}, follow_redirects=False)
    from tests.helpers import token_from_location

    token = token_from_location(start.headers["location"])
    code = _share_code(client, token)
    assert client.get(share_path(code)).status_code == 404


def test_shared_result_has_open_graph_tags(client):
    token = complete_session(client)
    code = _share_code(client, token)
    with db_session(client) as db:
        result_type = session_by_token(db, token).result_type

    html = client.get(share_path(code)).text

    assert 'property="og:image"' in html
    assert f"/static/images/og/{result_type}.png" in html
    assert 'content="summary_large_image"' in html
    assert 'property="og:image:width" content="1200"' in html


def test_shared_result_respects_language(client):
    token = complete_session(client)
    code = _share_code(client, token)

    uzbek = client.get(f"{share_path(code)}?lang=uz").text
    russian = client.get(f"{share_path(code)}?lang=ru").text

    assert "Ekstravert (E)" in uzbek
    # O'lchov yorliqlari ham tarjima qilinishi kerak — begona odam ko'radigan yagona sahifa.
    assert "Экстраверт (E)" in russian
    assert "Ekstravert (E)" not in russian


def test_shared_result_uses_russian_content_when_seeded(client):
    """Ulashish sahifasi — ruszabon tashrifchi ko'radigan birinchi sahifa."""
    from app.repositories.personality_repository import PersonalityRepository
    from app.seed.personality_placeholders import seed_personality_results

    token = complete_session(client)
    code = _share_code(client, token)
    with db_session(client) as db:
        seed_personality_results(db, language="ru")
        result_type = session_by_token(db, token).result_type
        repo = PersonalityRepository(db)
        ru_title = repo.get_result_content(result_type, "ru").title
        uz_title = repo.get_result_content(result_type, "uz").title
    assert ru_title != uz_title

    russian = client.get(f"{share_path(code)}?lang=ru").text
    assert ru_title in russian
    assert uz_title not in russian
    # Ulashilganda odam aynan og:title ni ko'radi — u ham ruscha bo'lishi shart.
    og_title = re.search(r'property="og:title" content="([^"]+)"', russian)
    assert og_title, "og:title topilmadi"
    assert ru_title in og_title.group(1)
    assert result_type in og_title.group(1)


def test_og_image_files_exist_for_every_type(client):
    """Ulashilgan har qanday natija uchun OG rasmi bo'lishi shart."""
    from app.seed.personality_placeholders import ALL_TYPES

    for mbti in ALL_TYPES:
        response = client.get(f"/static/images/og/{mbti}.png")
        assert response.status_code == 200, mbti
        assert response.headers["content-type"] == "image/png"


# --------------------------- natija sahifasidagi ulashish ---------------------------


def test_result_page_offers_referral_link(client):
    token = complete_session(client)
    html = client.get(f"/personality/result/{token}").text

    code = _share_code(client, token)
    assert f"/personality?ref={code}" in html, "natija sahifasida referal havolasi yo'q"


def test_telegram_share_url_encodes_parameters():
    url = telegram_share_url("https://example.uz/r/abc", "INFP — Vositachi")
    assert url.startswith("https://t.me/share/url?")
    assert "url=https%3A%2F%2Fexample.uz%2Fr%2Fabc" in url
    assert "INFP" in url


# --------------------------- test tarixi ---------------------------


def test_history_is_empty_before_any_test(client):
    response = client.get("/personality/history")
    assert response.status_code == 200
    assert "noindex" in response.text


def test_history_lists_completed_attempts(client):
    first = complete_session(client)
    client.post("/personality/restart", follow_redirects=False)
    second = complete_session(client)
    assert first != second

    html = client.get("/personality/history").text

    assert first in html
    assert second in html


def test_history_shows_shift_between_first_and_last_attempt(client):
    """Birinchi urinishda chap qutb, ikkinchisida o'ng qutb — farq ko'rsatilishi kerak."""
    from tests.helpers import favor_left_option_index, favor_right_option_index

    complete_session(client, option_picker=favor_left_option_index)
    client.post("/personality/restart", follow_redirects=False)
    complete_session(client, option_picker=favor_right_option_index)

    html = client.get("/personality/history").text

    # Qarama-qarshi javoblar berilgani uchun har o'lchov 0% dan 100% ga (yoki teskari) siljiydi.
    deltas = [int(value) for value in re.findall(r"\(([+-]\d+)\)", html)]
    assert len(deltas) == 4, f"to'rtta o'lchov kutilgan edi, topildi: {deltas}"
    assert all(abs(delta) == 100 for delta in deltas), deltas


def test_result_page_links_to_history_only_after_second_test(client):
    complete_session(client)
    assert "/personality/history" not in client.get("/personality/result/" + _last_token(client)).text

    client.post("/personality/restart", follow_redirects=False)
    second = complete_session(client)
    assert "/personality/history" in client.get(f"/personality/result/{second}").text


def _last_token(client) -> str:
    with db_session(client) as db:
        from tests.helpers import latest_session

        return latest_session(db).token

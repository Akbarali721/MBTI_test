"""Juftlik mosligi: sof hisob mantiqi va veb oqimi."""

import pytest

from app.i18n import TRANSLATIONS
from app.services.compatibility import (
    ALL_TYPES,
    compare_types,
    normalize_type,
    pair_slug,
    parse_pair_slug,
)
from tests.helpers import complete_session, db_session, session_by_token

# --------------------------- sof mantiq ---------------------------


def test_all_sixteen_types_are_generated():
    assert len(ALL_TYPES) == 16
    assert len(set(ALL_TYPES)) == 16
    assert "INFP" in ALL_TYPES and "ESTJ" in ALL_TYPES


def test_normalize_type_accepts_case_and_rejects_junk():
    assert normalize_type("infp") == "INFP"
    assert normalize_type("  EsTj ") == "ESTJ"
    assert normalize_type("XXXX") is None
    assert normalize_type("") is None
    assert normalize_type(None) is None


def test_identical_types_score_the_maximum():
    result = compare_types("INFP", "INFP")
    assert result.score == 100
    assert result.band == "high"
    assert all(dim.same for dim in result.dimensions)
    assert result.friction_keys == ()
    assert result.advice_keys == ("compat.advice.identical",)


def test_fully_opposite_types_still_score_above_forty():
    """Hech bir juftlik «mos emas» degan xulosa olmasligi kerak."""
    result = compare_types("INFP", "ESTJ")
    assert all(not dim.same for dim in result.dimensions)
    assert 40 < result.score < 62
    assert result.band == "growing"
    assert result.strength_keys == ("compat.strength.all_diff",)
    assert len(result.friction_keys) == 4


def test_score_is_symmetric_for_every_pair():
    for left in ALL_TYPES:
        for right in ALL_TYPES:
            assert compare_types(left, right).score == compare_types(right, left).score


def test_score_stays_within_bounds_for_every_pair():
    scores = [compare_types(a, b).score for a in ALL_TYPES for b in ALL_TYPES]
    assert max(scores) == 100
    assert min(scores) >= 40


def test_sn_mismatch_costs_more_than_ei_mismatch():
    """S/N — bir-birini tushunish uchun eng muhim o'lchov, vazni eng katta bo'lishi kerak."""
    sn_differs = compare_types("ISTJ", "INTJ")
    ei_differs = compare_types("ISTJ", "ESTJ")
    assert sn_differs.score < ei_differs.score


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        compare_types("INFP", "ZZZZ")


def test_pair_slug_roundtrip():
    assert pair_slug("infp", "estj") == "INFP-ESTJ"
    assert parse_pair_slug("INFP-ESTJ") == ("INFP", "ESTJ")
    assert parse_pair_slug("infp-estj") == ("INFP", "ESTJ")
    assert parse_pair_slug("INFP") is None
    assert parse_pair_slug("INFP-ZZZZ") is None
    assert parse_pair_slug("") is None


def test_every_referenced_translation_key_exists():
    """Har juftlik uchun ishlatiladigan kalitlar ikkala katalogda ham bo'lishi shart."""
    keys: set[str] = set()
    for left in ALL_TYPES:
        for right in ALL_TYPES:
            result = compare_types(left, right)
            keys.update(dim.text_key for dim in result.dimensions)
            keys.update(result.strength_keys)
            keys.update(result.friction_keys)
            keys.update(result.advice_keys)
            keys.add(f"compat.band_{result.band}")
            keys.add(f"compat.band_{result.band}_desc")
            keys.add(f"compat.band_{result.band}_short")

    for lang in ("uz", "ru"):
        missing = sorted(key for key in keys if key not in TRANSLATIONS[lang])
        assert not missing, f"{lang} katalogida yo'q: {missing}"


# --------------------------- veb oqimi ---------------------------


def test_index_renders_the_form(client):
    page = client.get("/relationship")
    assert page.status_code == 200
    assert 'name="left_type"' in page.text
    assert 'name="right_type"' in page.text
    assert page.text.count("<option") >= 33  # 16 tip x 2 select + ikkita "tanlang"


def test_index_preselects_the_visitors_own_type(client):
    token = complete_session(client)
    with db_session(client) as db:
        result_type = session_by_token(db, token).result_type

    page = client.get("/relationship")
    assert f'value="{result_type}" selected' in page.text


def test_compare_redirects_to_a_shareable_url(client):
    response = client.post(
        "/relationship/compare",
        data={"left_type": "INFP", "right_type": "ESTJ"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/relationship/INFP-ESTJ"


def test_compare_rejects_an_unknown_type(client):
    response = client.post(
        "/relationship/compare",
        data={"left_type": "INFP", "right_type": "ZZZZ"},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert 'name="left_type"' in response.text


def test_result_page_shows_score_and_both_types(client):
    page = client.get("/relationship/INFP-ESTJ")
    assert page.status_code == 200
    assert "INFP" in page.text and "ESTJ" in page.text
    assert f"{compare_types('INFP', 'ESTJ').score}%" in page.text


def test_result_page_is_reachable_without_a_session(client):
    """Ulashilgan havolani begona odam ham ocha olishi kerak."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as stranger:
        assert stranger.get("/relationship/ENFJ-ISTP").status_code == 200


def test_result_page_404_for_a_bad_pair(client):
    assert client.get("/relationship/INFP-ZZZZ").status_code == 404
    assert client.get("/relationship/nonsense").status_code == 404


def test_result_page_is_translated(client):
    russian = client.get("/relationship/INFP-ESTJ?lang=ru").text
    assert "Совместимость" in russian or "совместимость" in russian
    assert "Juftlik mosligi" not in russian

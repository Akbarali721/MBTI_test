"""Rivojlanish yo‘nalishlari va natija sahifasi oqimi."""

from app.seed.growth_guidance_schema import format_action_plan
from app.seed.personality_guidance_uz import PERSONALITY_GROWTH_UZ
from app.seed.personality_placeholders import ALL_TYPES
from app.seed.personality_results_uz import GENERIC_FALLBACK, get_result_copy


def test_all_types_have_two_growth_areas_with_seven_days():
    assert set(PERSONALITY_GROWTH_UZ.keys()) == set(ALL_TYPES)
    for ptype in ALL_TYPES:
        areas = PERSONALITY_GROWTH_UZ[ptype]
        assert len(areas) == 2
        ids = {a["id"] for a in areas}
        assert len(ids) == 2
        for area in areas:
            assert area["today_task"]
            assert area["success_criteria"]
            assert len(area["steps"]) <= 3
            assert len(area["week_plan"]) == 7
            for day in area["week_plan"]:
                assert 1 <= day["day"] <= 7


def test_get_result_copy_merges_challenges_and_plan():
    copy = get_result_copy("ENTP")
    areas = PERSONALITY_GROWTH_UZ["ENTP"]
    assert copy["challenges"] == [areas[0]["name"], areas[1]["name"]]
    assert copy["action_plan"] == format_action_plan(areas[0])
    assert "1-kun:" in copy["action_plan"]
    assert "2-hafta" not in copy["action_plan"]


def test_unknown_type_uses_neutral_fallback_without_growth_names():
    copy = get_result_copy("XXXX")
    assert copy == GENERIC_FALLBACK
    assert "ikki barobar" not in copy["short_description"].lower()


def test_result_page_shows_try_today_for_free_user(client):
    from tests.helpers import complete_session

    token = complete_session(client)
    html = client.get(f"/personality/result/{token}").text
    assert "Bugun sinab ko‘ring" in html or "Bugun sinab ko" in html
    assert "growth-today-data" in html
    assert "growth-week-data" not in html


def test_focus_query_does_not_change_type_on_page(client):
    import re

    from tests.helpers import complete_session

    token = complete_session(client)
    base = client.get(f"/personality/result/{token}").text
    match = re.search(r"Tip:\s*([A-Z]{4})", base)
    assert match, "tip kodi sahifada ko‘rinmadi"
    ptype = match.group(1)
    areas = PERSONALITY_GROWTH_UZ[ptype]
    other = areas[1]["id"]
    focused = client.get(f"/personality/result/{token}?focus={other}").text
    assert areas[1]["name"] in focused
    assert f"Tip: {ptype}" in focused or f"Tip:  {ptype}" in focused

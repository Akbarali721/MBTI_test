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


def test_get_result_copy_merges_plan_and_daily_tips():
    copy = get_result_copy("ENTP")
    areas = PERSONALITY_GROWTH_UZ["ENTP"]
    assert copy["daily_tips"] == areas[0]["steps"][:3]
    assert copy["action_plan"] == format_action_plan(areas[0])
    assert "1-kun:" in copy["action_plan"]
    assert "2-hafta" not in copy["action_plan"]


def test_unknown_type_uses_neutral_fallback_without_growth_names():
    copy = get_result_copy("XXXX")
    assert copy == GENERIC_FALLBACK
    assert "ikki barobar" not in copy["short_description"].lower()


def test_result_page_shows_daily_tips_for_free_user(client):
    from app.i18n import t
    from tests.helpers import complete_session, session_by_token, db_session

    token = complete_session(client)
    html = client.get(f"/personality/result/{token}").text
    assert t("result.daily_tips", "uz") in html
    assert "growth-week-data" not in html
    with db_session(client) as db:
        ptype = session_by_token(db, token).result_type
    tips = get_result_copy(ptype)["daily_tips"]
    assert tips[0] in html


def test_focus_query_does_not_break_free_result_page(client):
    from tests.helpers import complete_session, session_by_token, db_session

    token = complete_session(client)
    with db_session(client) as db:
        ptype = session_by_token(db, token).result_type
    areas = PERSONALITY_GROWTH_UZ[ptype]
    other = areas[1]["id"]
    focused = client.get(f"/personality/result/{token}?focus={other}").text
    assert "Tip:" not in focused
    assert get_result_copy(ptype)["daily_tips"][0] in focused

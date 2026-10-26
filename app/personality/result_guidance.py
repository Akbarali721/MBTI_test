"""Natija sahifasi uchun rivojlanish yo‘nalishlari (matn bazadan emas, seed moduldan)."""

from __future__ import annotations

from app.models.personality import DEFAULT_CONTENT_LANGUAGE
from app.seed.growth_guidance_schema import GrowthArea, format_action_plan
from app.seed.personality_guidance_uz import PERSONALITY_GROWTH_UZ


def get_growth_areas(personality_type: str, *, language: str) -> tuple[GrowthArea, GrowthArea] | None:
    if language != DEFAULT_CONTENT_LANGUAGE:
        return None
    key = (personality_type or "").upper()
    pair = PERSONALITY_GROWTH_UZ.get(key)
    if not pair:
        return None
    return pair[0], pair[1]


def resolve_focus_area(
    areas: tuple[GrowthArea, GrowthArea],
    focus_id: str | None,
) -> GrowthArea:
    if focus_id:
        for area in areas:
            if area["id"] == focus_id:
                return area
    return areas[0]


def public_today_card(area: GrowthArea) -> dict[str, str | list[str]]:
    """Bepul foydalanuvchiga faqat bugungi vazifa kartasi."""
    return {
        "area_id": area["id"],
        "area_name": area["name"],
        "situation": area["situation"],
        "method": area["method"],
        "steps": area["steps"],
        "today_task": area["today_task"],
        "success_criteria": area["success_criteria"],
        "lighter_variant": area["lighter_variant"],
        "check_question": area["check_question"],
    }


def premium_week_plan(area: GrowthArea) -> list[dict[str, str | int]]:
    return [
        {
            "day": day["day"],
            "task": day["task"],
            "minutes": day["minutes"],
            "success": day["success"],
        }
        for day in area["week_plan"]
    ]


def action_plan_text(area: GrowthArea) -> str:
    return format_action_plan(area)

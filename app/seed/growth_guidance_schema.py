"""Rivojlanish yo‘nalishi va 7 kunlik reja uchun tuzilma (faqat kod, matn emas)."""

from typing import TypedDict


class PlanDay(TypedDict):
    day: int
    task: str
    minutes: str
    success: str


class GrowthArea(TypedDict):
    id: str
    name: str
    situation: str
    method: str
    steps: list[str]
    today_task: str
    success_criteria: str
    lighter_variant: str
    check_question: str
    week_plan: list[PlanDay]


def format_action_plan(area: GrowthArea) -> str:
    """DB va premium uchun yagona matn manbai — 1–7 kun."""
    parts: list[str] = []
    for day in area["week_plan"]:
        success = day["success"].rstrip(".")
        parts.append(
            f"{day['day']}-kun: {day['task']} ({day['minutes']}). "
            f"{success}."
        )
    return " ".join(parts)


def week_from_rows(rows: list[tuple[str, str, str]]) -> list[PlanDay]:
    if len(rows) != 7:
        raise ValueError("week_plan aynan 7 kun bo‘lishi kerak")
    return [
        PlanDay(day=i + 1, task=task, minutes=minutes, success=success)
        for i, (task, minutes, success) in enumerate(rows)
    ]

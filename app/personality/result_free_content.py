"""Bepul natija bo‘limlari uchun matn (DB o‘zgartirilmaydi, seed provayderdan olinadi)."""

from __future__ import annotations

from app.seed.personality_placeholders import result_copy_provider


def free_result_sections(personality_type: str, *, language: str) -> tuple[list[str], list[str]]:
    """Ikki qiyin holat va uch amaliy tavsiya — tip bo‘yicha seed dan."""
    provider = result_copy_provider(language)
    copy = provider((personality_type or "").upper())
    challenges = [c for c in copy.get("challenges", []) if c][:2]
    tips = [t for t in copy.get("daily_tips", []) if t][:3]
    return challenges, tips

"""Visual theme configuration for personality test (Variant A)."""

from app.models.enums import AppearanceTheme
from app.models.personality import PersonalityTestSession

SELECTABLE_APPEARANCE_THEMES = (AppearanceTheme.MALE, AppearanceTheme.FEMALE)
SELECTABLE_APPEARANCE_VALUES = frozenset(theme.value for theme in SELECTABLE_APPEARANCE_THEMES)

PERSONALITY_SESSION_COOKIE_KEY = "personality_token"


def has_appearance_choice(session: PersonalityTestSession) -> bool:
    return session.appearance_theme in SELECTABLE_APPEARANCE_THEMES


def resolve_theme_key(session: PersonalityTestSession | None) -> str:
    if session is None or session.appearance_theme not in SELECTABLE_APPEARANCE_THEMES:
        return AppearanceTheme.MALE.value
    return session.appearance_theme.value


def theme_template_context(session: PersonalityTestSession | None) -> dict[str, str]:
    if session is None or not has_appearance_choice(session):
        return {"theme_class": "", "theme_key": "", "gender": ""}
    key = session.appearance_theme.value  # type: ignore[union-attr]
    return {"theme_class": f"theme-{key}", "theme_key": key, "gender": key}

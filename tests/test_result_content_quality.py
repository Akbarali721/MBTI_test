"""Natija kontenti sifat kafolatlari.

Premium bo‘limlar aynan shu narsa uchun pul to‘lanadi. Bir paytlar o‘zbekcha
matnlar barcha 16 tur uchun bir xil shablon edi (faqat tip nomi almashardi) —
shu test o‘sha holatga qaytishga yo‘l qo‘ymaydi.
"""

import pytest

from app.seed.personality_placeholders import ALL_TYPES, RESULT_COPY_PROVIDERS, SEED_LANGUAGES
from app.seed.personality_results_uz import ResultCopy

PREMIUM_FIELDS = (
    "motivation_analysis",
    "work_style",
    "career_environment",
    "friendship_style",
    "relationship_needs",
    "compatible_people",
    "difficult_communication",
    "action_plan",
)
FREE_FIELDS = ("title", "short_description", "public_view")
MIN_PREMIUM_LENGTH = 80


@pytest.mark.parametrize("language", SEED_LANGUAGES)
def test_every_type_has_content_in_every_language(language):
    provider = RESULT_COPY_PROVIDERS[language]
    for ptype in ALL_TYPES:
        copy = provider(ptype)
        assert set(copy) == set(ResultCopy.__annotations__), f"{language}/{ptype} maydonlari mos emas"
        assert copy["strengths"] and copy["challenges"], f"{language}/{ptype} ro‘yxatlari bo‘sh"


@pytest.mark.parametrize("language", SEED_LANGUAGES)
@pytest.mark.parametrize("field", PREMIUM_FIELDS)
def test_premium_sections_are_unique_per_type(language, field):
    """Har turga alohida matn: takror = pullik kontent aslida bir xil degani."""
    provider = RESULT_COPY_PROVIDERS[language]
    seen: dict[str, str] = {}
    for ptype in ALL_TYPES:
        text = provider(ptype)[field]
        assert len(text) >= MIN_PREMIUM_LENGTH, f"{language}/{ptype}/{field} juda qisqa"
        duplicate = seen.get(text)
        assert duplicate is None, f"{language}/{field}: {ptype} va {duplicate} matni bir xil"
        seen[text] = ptype


@pytest.mark.parametrize("language", SEED_LANGUAGES)
@pytest.mark.parametrize("field", FREE_FIELDS)
def test_free_sections_are_unique_per_type(language, field):
    provider = RESULT_COPY_PROVIDERS[language]
    values = {provider(ptype)[field] for ptype in ALL_TYPES}
    assert len(values) == len(ALL_TYPES), f"{language}/{field} matnlari takrorlanmoqda"


def test_premium_text_does_not_lean_on_the_type_code():
    """Matn «INFP tipi uchun» kabi shablon bilan emas, mazmun bilan farqlanishi kerak."""
    provider = RESULT_COPY_PROVIDERS["uz"]
    for ptype in ALL_TYPES:
        copy = provider(ptype)
        for field in PREMIUM_FIELDS:
            assert ptype not in copy[field], f"uz/{ptype}/{field} tip kodiga tayanmoqda"


def test_uzbek_text_uses_the_project_apostrophes():
    """Loyihada oʻ/gʻ uchun U+2018, tutuq belgisi uchun U+2019 ishlatiladi."""
    provider = RESULT_COPY_PROVIDERS["uz"]
    for ptype in ALL_TYPES:
        copy = provider(ptype)
        for field, value in copy.items():
            chunks = value if isinstance(value, list) else [value]
            for chunk in chunks:
                assert "'" not in chunk, f"uz/{ptype}/{field} da ASCII apostrof bor"
                assert "`" not in chunk, f"uz/{ptype}/{field} da teskari apostrof bor"

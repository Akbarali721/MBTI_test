"""Unit tests for 012 question-variant unique constraint discovery (no DB required)."""

import importlib.util
from pathlib import Path

_REVISION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "012_question_variants.py"
_spec = importlib.util.spec_from_file_location("migration_012", _REVISION_PATH)
assert _spec and _spec.loader
m012 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m012)


def test_find_unique_detects_postgresql_default_order_number_constraint_name():
    constraints = [{"name": "personality_questions_order_number_key", "column_names": ["order_number"]}]
    found = m012.find_unique_names_for_columns(constraints, [], ("order_number",))
    assert found == [("constraint", "personality_questions_order_number_key")]


def test_find_unique_detects_differently_named_order_number_constraint():
    constraints = [{"name": "uq_personality_questions_order_number", "column_names": ["order_number"]}]
    found = m012.find_unique_names_for_columns(constraints, [], ("order_number",))
    assert found == [("constraint", "uq_personality_questions_order_number")]


def test_find_unique_detects_unique_index_only_on_order_number():
    indexes = [{"name": "personality_questions_order_number_key", "unique": True, "column_names": ["order_number"]}]
    found = m012.find_unique_names_for_columns([], indexes, ("order_number",))
    assert found == [("index", "personality_questions_order_number_key")]


def test_find_unique_skips_when_no_order_number_singleton():
    constraints = [{"name": "uq_question_variant_order", "column_names": ["variant", "order_number"]}]
    assert m012.find_unique_names_for_columns(constraints, [], ("order_number",)) == []


def test_find_unique_does_not_match_by_substring_in_name():
    """Regression: old code dropped anything with 'order_number' in the constraint name."""
    constraints = [{"name": "uq_question_variant_order", "column_names": ["variant", "order_number"]}]
    indexes = [{"name": "ix_personality_questions_order_number", "unique": False, "column_names": ["order_number"]}]
    assert m012.find_unique_names_for_columns(constraints, indexes, ("order_number",)) == []

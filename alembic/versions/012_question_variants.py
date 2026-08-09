"""Savol banki va A/B test: savol hamda sessiyaga variant ustuni

Revision ID: 012_variants
Revises: 011_teams

order_number endi global emas, to'plam ichida noyob — shuning uchun bir nechta
savol to'plami yonma-yon yashay oladi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "012_variants"
down_revision: Union[str, None] = "011_teams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUESTIONS = "personality_questions"
SESSIONS = "personality_test_sessions"
COLUMN = "variant"
DEFAULT = "A"
NEW_UNIQUE = "uq_question_variant_order"
QUESTIONS_VARIANT_INDEX = "ix_personality_questions_variant"
ORDER_NUMBER_ONLY = ("order_number",)


def _bind():
    return op.get_bind()


def _dialect_name() -> str:
    return _bind().dialect.name


def _inspector():
    return inspect(_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(col["name"] == name for col in _inspector().get_columns(table))


def _index_names(table: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table) if idx.get("name")}


def _column_tuple(columns: list[str] | None) -> tuple[str, ...]:
    return tuple(columns or ())


def find_unique_names_for_columns(
    unique_constraints: list[dict],
    indexes: list[dict],
    columns: tuple[str, ...],
) -> list[tuple[str, str]]:
    """Return (kind, name) pairs: kind is 'constraint' or 'index'."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for uc in unique_constraints:
        name = uc.get("name")
        if not name or name in seen:
            continue
        if _column_tuple(uc.get("column_names")) == columns:
            found.append(("constraint", name))
            seen.add(name)
    for idx in indexes:
        if not idx.get("unique"):
            continue
        name = idx.get("name")
        if not name or name in seen:
            continue
        if _column_tuple(idx.get("column_names")) == columns:
            found.append(("index", name))
            seen.add(name)
    return found


def _unique_names_for_columns(table: str, columns: tuple[str, ...]) -> list[tuple[str, str]]:
    insp = _inspector()
    return find_unique_names_for_columns(
        insp.get_unique_constraints(table),
        insp.get_indexes(table),
        columns,
    )


def _variant_order_unique_present(table: str) -> bool:
    return bool(_unique_names_for_columns(table, (COLUMN, "order_number")))


def _questions_target() -> sa.Table:
    """Jadvalning KERAKLI ko'rinishi — SQLite'da qayta qurish uchun.

    001 migratsiyasi `UNIQUE (order_number)` ni NOMSIZ yaratgan, shuning uchun uni
    nom bo'yicha tashlab bo'lmaydi; jadval shu ta'rif bo'yicha qaytadan quriladi.
    """
    metadata = sa.MetaData()
    return sa.Table(
        QUESTIONS,
        metadata,
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("dimension", sa.String(length=2), nullable=False),
        sa.Column("order_number", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("variant", sa.String(length=8), nullable=False, server_default=DEFAULT),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(COLUMN, "order_number", name=NEW_UNIQUE),
        sa.Index(QUESTIONS_VARIANT_INDEX, COLUMN),
    )


def _add_variant(table: str, index_name: str) -> None:
    if _has_column(table, COLUMN):
        return
    op.add_column(
        table,
        sa.Column(COLUMN, sa.String(length=8), nullable=False, server_default=DEFAULT),
    )
    if index_name not in _index_names(table):
        op.create_index(index_name, table, [COLUMN])


def _drop_order_number_singleton_uniques_postgresql() -> None:
    """Remove UNIQUE(order_number) whether stored as constraint and/or unique index."""
    for kind, name in _unique_names_for_columns(QUESTIONS, ORDER_NUMBER_ONLY):
        if name == NEW_UNIQUE:
            continue
        if kind == "constraint":
            _bind().execute(
                text(f'ALTER TABLE {QUESTIONS} DROP CONSTRAINT IF EXISTS "{name}"')
            )
        else:
            _bind().execute(text(f'DROP INDEX IF EXISTS "{name}"'))


def _ensure_variant_order_unique_postgresql() -> None:
    if _variant_order_unique_present(QUESTIONS):
        return
    op.create_unique_constraint(NEW_UNIQUE, QUESTIONS, [COLUMN, "order_number"])


def _upgrade_questions_sqlite() -> None:
    if not _has_column(QUESTIONS, COLUMN):
        op.add_column(
            QUESTIONS,
            sa.Column(COLUMN, sa.String(length=8), nullable=False, server_default=DEFAULT),
        )
    if _variant_order_unique_present(QUESTIONS):
        if QUESTIONS_VARIANT_INDEX not in _index_names(QUESTIONS):
            op.create_index(QUESTIONS_VARIANT_INDEX, QUESTIONS, [COLUMN])
        return
    with op.batch_alter_table(QUESTIONS, copy_from=_questions_target(), recreate="always"):
        pass


def _upgrade_questions_postgresql() -> None:
    if _has_column(QUESTIONS, COLUMN) and _variant_order_unique_present(QUESTIONS):
        if QUESTIONS_VARIANT_INDEX not in _index_names(QUESTIONS):
            op.create_index(QUESTIONS_VARIANT_INDEX, QUESTIONS, [COLUMN])
        return

    _add_variant(QUESTIONS, QUESTIONS_VARIANT_INDEX)
    _drop_order_number_singleton_uniques_postgresql()
    _ensure_variant_order_unique_postgresql()


def upgrade() -> None:
    if _has_table(QUESTIONS):
        if _dialect_name() == "sqlite":
            _upgrade_questions_sqlite()
        else:
            _upgrade_questions_postgresql()

    if _has_table(SESSIONS):
        _add_variant(SESSIONS, "ix_personality_test_sessions_variant")


def downgrade() -> None:
    if _has_table(SESSIONS) and _has_column(SESSIONS, COLUMN):
        if "ix_personality_test_sessions_variant" in _index_names(SESSIONS):
            op.drop_index("ix_personality_test_sessions_variant", table_name=SESSIONS)
        op.drop_column(SESSIONS, COLUMN)

    if not _has_table(QUESTIONS) or not _has_column(QUESTIONS, COLUMN):
        return

    op.execute(sa.text(f"DELETE FROM {QUESTIONS} WHERE {COLUMN} <> '{DEFAULT}'"))

    if _dialect_name() == "sqlite":
        with op.batch_alter_table(QUESTIONS, copy_from=_questions_target()) as batch:
            batch.drop_constraint(NEW_UNIQUE, type_="unique")
            batch.create_unique_constraint("uq_personality_questions_order_number", ["order_number"])
            batch.drop_index(QUESTIONS_VARIANT_INDEX)
            batch.drop_column(COLUMN)
        return

    for kind, name in _unique_names_for_columns(QUESTIONS, (COLUMN, "order_number")):
        if kind == "constraint":
            _bind().execute(text(f'ALTER TABLE {QUESTIONS} DROP CONSTRAINT IF EXISTS "{name}"'))
        else:
            _bind().execute(text(f'DROP INDEX IF EXISTS "{name}"'))
    if QUESTIONS_VARIANT_INDEX in _index_names(QUESTIONS):
        op.drop_index(QUESTIONS_VARIANT_INDEX, table_name=QUESTIONS)
    op.drop_column(QUESTIONS, COLUMN)
    if not _unique_names_for_columns(QUESTIONS, ORDER_NUMBER_ONLY):
        op.create_unique_constraint("uq_personality_questions_order_number", QUESTIONS, ["order_number"])

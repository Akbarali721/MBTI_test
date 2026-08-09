"""Savol banki va A/B test: savol hamda sessiyaga variant ustuni

Revision ID: 012_variants
Revises: 011_teams

order_number endi global emas, to'plam ichida noyob — shuning uchun bir nechta
savol to'plami yonma-yon yashay oladi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

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
OLD_UNIQUE = "uq_personality_questions_order_number"


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(col["name"] == name for col in inspect(op.get_bind()).get_columns(table))


def _unique_constraints(table: str) -> list[str]:
    inspector = inspect(op.get_bind())
    names = [c["name"] for c in inspector.get_unique_constraints(table) if c["name"]]
    names += [i["name"] for i in inspector.get_indexes(table) if i["unique"] and i["name"]]
    return names


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
        # Indeks ham shu ta'rifda bo'lishi shart: qayta qurishda e'lon qilinmagani yo'qoladi.
        sa.Index(QUESTIONS_VARIANT_INDEX, COLUMN),
    )


def _add_variant(table: str, index_name: str) -> None:
    if _has_column(table, COLUMN):
        return
    op.add_column(
        table,
        sa.Column(COLUMN, sa.String(length=8), nullable=False, server_default=DEFAULT),
    )
    op.create_index(index_name, table, [COLUMN])


def upgrade() -> None:
    if _has_table(QUESTIONS):
        # order_number'ning yakka o'zi noyob bo'lsa, ikkinchi to'plam sig'maydi.
        if op.get_bind().dialect.name == "sqlite":
            # 001 dagi UNIQUE(order_number) nomsiz — uni faqat jadvalni qayta qurib
            # olib tashlash mumkin. Ustun avval qo'shiladi, indeks ta'rif bilan keladi.
            if not _has_column(QUESTIONS, COLUMN):
                op.add_column(
                    QUESTIONS,
                    sa.Column(COLUMN, sa.String(length=8), nullable=False, server_default=DEFAULT),
                )
            with op.batch_alter_table(QUESTIONS, copy_from=_questions_target(), recreate="always"):
                pass
        else:
            _add_variant(QUESTIONS, QUESTIONS_VARIANT_INDEX)
            existing = _unique_constraints(QUESTIONS)
            with op.batch_alter_table(QUESTIONS) as batch:
                for name in existing:
                    if "order_number" in name and name != NEW_UNIQUE:
                        batch.drop_constraint(name, type_="unique")
                if NEW_UNIQUE not in existing:
                    batch.create_unique_constraint(NEW_UNIQUE, [COLUMN, "order_number"])

    if _has_table(SESSIONS):
        _add_variant(SESSIONS, "ix_personality_test_sessions_variant")


def downgrade() -> None:
    if _has_table(SESSIONS) and _has_column(SESSIONS, COLUMN):
        op.drop_index("ix_personality_test_sessions_variant", table_name=SESSIONS)
        op.drop_column(SESSIONS, COLUMN)

    if _has_table(QUESTIONS) and _has_column(QUESTIONS, COLUMN):
        # Faqat bitta to'plam qolishi kerak, aks holda order_number takrorlanadi.
        op.execute(sa.text(f"DELETE FROM {QUESTIONS} WHERE {COLUMN} <> '{DEFAULT}'"))
        with op.batch_alter_table(QUESTIONS, copy_from=_questions_target()) as batch:
            batch.drop_constraint(NEW_UNIQUE, type_="unique")
            batch.create_unique_constraint(OLD_UNIQUE, ["order_number"])
            batch.drop_index(QUESTIONS_VARIANT_INDEX)
            batch.drop_column(COLUMN)

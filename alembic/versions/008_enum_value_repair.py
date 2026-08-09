"""Repair enum labels stored by create_all (member names instead of values)

Revision ID: 008_enum_repair
Revises: 007_payment_status

create_all bilan qurilgan bazalarda sa.Enum a'zo NOMINI saqlagan ("VISITED"),
model esa endi values_callable orqali QIYMATNI ("visited") kutadi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "008_enum_repair"
down_revision: Union[str, None] = "007_payment_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSION_TABLE = "personality_test_sessions"

STATUS_MAP = {
    "VISITED": "visited",
    "STARTED": "started",
    "IN_PROGRESS": "in_progress",
    "COMPLETED": "completed",
}
THEME_MAP = {
    "MALE": "male",
    "FEMALE": "female",
    "NEUTRAL": "neutral",
}


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspect(op.get_bind()).get_columns(table_name)}


def _pg_type_exists(type_name: str) -> bool:
    result = op.get_bind().execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"), {"name": type_name}
    )
    return result.first() is not None


def _pg_add_labels(type_name: str, labels: list[str]) -> None:
    if not _pg_type_exists(type_name):
        return
    # Yangi label qo'shilgan tranzaksiyada undan foydalanib bo'lmaydi, shuning uchun autocommit.
    with op.get_context().autocommit_block():
        for label in labels:
            op.execute(sa.text(f"ALTER TYPE {type_name} ADD VALUE IF NOT EXISTS '{label}'"))


def _repair_postgres() -> None:
    _pg_add_labels("personality_session_status", list(STATUS_MAP.values()))
    _pg_add_labels("appearance_theme", list(THEME_MAP.values()))

    for old, new in STATUS_MAP.items():
        op.execute(
            sa.text(
                f"UPDATE {SESSION_TABLE} SET status = '{new}'::personality_session_status "
                f"WHERE status::text = '{old}'"
            )
        )
    if _has_column(SESSION_TABLE, "appearance_theme"):
        for old, new in THEME_MAP.items():
            op.execute(
                sa.text(
                    f"UPDATE {SESSION_TABLE} SET appearance_theme = '{new}'::appearance_theme "
                    f"WHERE appearance_theme::text = '{old}'"
                )
            )


def _repair_text_columns() -> None:
    for old, new in STATUS_MAP.items():
        op.execute(sa.text(f"UPDATE {SESSION_TABLE} SET status = '{new}' WHERE status = '{old}'"))
    if _has_column(SESSION_TABLE, "appearance_theme"):
        for old, new in THEME_MAP.items():
            op.execute(
                sa.text(
                    f"UPDATE {SESSION_TABLE} SET appearance_theme = '{new}' WHERE appearance_theme = '{old}'"
                )
            )


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        _repair_postgres()
    else:
        _repair_text_columns()


def downgrade() -> None:
    # Qiymatlarni katta harfga qaytarish ma'nosiz: model faqat kichik harfni tushunadi.
    pass

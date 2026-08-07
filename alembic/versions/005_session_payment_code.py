"""Persistent payment_code column for personality sessions

Revision ID: 005_payment_code
Revises: 004_premium_payment
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "005_payment_code"
down_revision: Union[str, None] = "004_premium_payment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_test_sessions"
INDEX = "ix_personality_test_sessions_payment_code"
MIN_LENGTH = 8
MAX_LENGTH = 16


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspect(op.get_bind()).get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    return index_name in {ix["name"] for ix in inspect(op.get_bind()).get_indexes(table_name)}


def _backfill() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(f"SELECT id, token FROM {TABLE} WHERE payment_code IS NULL ORDER BY id")
    ).fetchall()
    taken: set[str] = {
        row[0]
        for row in bind.execute(
            sa.text(f"SELECT payment_code FROM {TABLE} WHERE payment_code IS NOT NULL")
        ).fetchall()
        if row[0]
    }
    for session_id, token in rows:
        normalized = (token or "").strip().lower()
        if not normalized:
            continue
        code = normalized[:MAX_LENGTH]
        for length in range(MIN_LENGTH, min(len(normalized), MAX_LENGTH) + 1):
            candidate = normalized[:length]
            if candidate not in taken:
                code = candidate
                break
        taken.add(code)
        bind.execute(
            sa.text(f"UPDATE {TABLE} SET payment_code = :code WHERE id = :id"),
            {"code": code, "id": session_id},
        )


def upgrade() -> None:
    if not _has_column(TABLE, "payment_code"):
        op.add_column(TABLE, sa.Column("payment_code", sa.String(length=16), nullable=True))
    _backfill()
    if not _has_index(TABLE, INDEX):
        op.create_index(INDEX, TABLE, ["payment_code"], unique=True)


def downgrade() -> None:
    if _has_index(TABLE, INDEX):
        op.drop_index(INDEX, table_name=TABLE)
    if _has_column(TABLE, "payment_code"):
        op.drop_column(TABLE, "payment_code")

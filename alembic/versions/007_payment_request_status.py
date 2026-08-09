"""payment_requests: status CHECK, nullable telegram_user_id, no amount default

Revision ID: 007_payment_status
Revises: 006_result_language
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "007_payment_status"
down_revision: Union[str, None] = "006_result_language"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "payment_requests"
TMP_TABLE = "payment_requests_tmp_007"
CHECK_NAME = "ck_payment_requests_status"
ALLOWED_STATUSES = ("pending", "receipt_sent", "approved", "rejected")

COPY_COLUMNS = (
    "id",
    "session_id",
    "telegram_user_id",
    "telegram_username",
    "telegram_first_name",
    "amount",
    "status",
    "receipt_file_id",
    "receipt_type",
    "created_at",
    "receipt_sent_at",
    "approved_at",
    "rejected_at",
    "approved_by",
)


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_check(table_name: str, name: str) -> bool:
    return name in {ck["name"] for ck in inspect(op.get_bind()).get_check_constraints(table_name)}


def _check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in ALLOWED_STATUSES)
    return f"status IN ({values})"


def _normalize_statuses() -> None:
    op.execute(sa.text(f"UPDATE {TABLE} SET status = lower(status) WHERE status <> lower(status)"))
    allowed = ", ".join(f"'{value}'" for value in ALLOWED_STATUSES)
    op.execute(sa.text(f"UPDATE {TABLE} SET status = 'pending' WHERE status NOT IN ({allowed})"))


def _new_table_columns() -> list:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_username", sa.String(length=64), nullable=True),
        sa.Column("telegram_first_name", sa.String(length=128), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("receipt_file_id", sa.String(length=256), nullable=True),
        sa.Column("receipt_type", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("receipt_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["personality_test_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(_check_sql(), name=CHECK_NAME),
    ]


def _recreate_sqlite() -> None:
    # SQLite CHECK qo'shish, NULL ruxsati va DEFAULT olib tashlash uchun jadvalni qayta quradi.
    op.create_table(TMP_TABLE, *_new_table_columns())
    columns = ", ".join(COPY_COLUMNS)
    op.execute(sa.text(f"INSERT INTO {TMP_TABLE} ({columns}) SELECT {columns} FROM {TABLE}"))
    op.drop_table(TABLE)
    op.rename_table(TMP_TABLE, TABLE)
    op.create_index("ix_payment_requests_session_id", TABLE, ["session_id"])
    op.create_index("ix_payment_requests_telegram_user_id", TABLE, ["telegram_user_id"])
    op.create_index("ix_payment_requests_status", TABLE, ["status"])


def _alter_generic() -> None:
    op.alter_column(TABLE, "amount", existing_type=sa.Integer(), server_default=None)
    op.alter_column(
        TABLE,
        "telegram_user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    if not _has_check(TABLE, CHECK_NAME):
        op.create_check_constraint(CHECK_NAME, TABLE, _check_sql())


def upgrade() -> None:
    if not _has_table(TABLE):
        return
    _normalize_statuses()
    if _has_check(TABLE, CHECK_NAME):
        return
    if op.get_bind().dialect.name == "sqlite":
        _recreate_sqlite()
    else:
        _alter_generic()


def downgrade() -> None:
    if not _has_table(TABLE):
        return
    if op.get_bind().dialect.name == "sqlite":
        return
    if _has_check(TABLE, CHECK_NAME):
        op.drop_constraint(CHECK_NAME, TABLE, type_="check")
    op.execute(sa.text(f"UPDATE {TABLE} SET telegram_user_id = 0 WHERE telegram_user_id IS NULL"))
    op.alter_column(TABLE, "telegram_user_id", existing_type=sa.BigInteger(), nullable=False)
    op.alter_column(TABLE, "amount", existing_type=sa.Integer(), server_default="9999")

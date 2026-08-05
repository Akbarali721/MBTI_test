"""Premium payment flow fields and payment_requests table

Revision ID: 004_premium_payment
Revises: 003_session_analytics
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "004_premium_payment"
down_revision: Union[str, None] = "003_session_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def upgrade() -> None:
    session_cols = [
        ("telegram_username", sa.Column("telegram_username", sa.String(length=64), nullable=True)),
        ("telegram_first_name", sa.Column("telegram_first_name", sa.String(length=128), nullable=True)),
        ("premium_requested_at", sa.Column("premium_requested_at", sa.DateTime(timezone=True), nullable=True)),
        ("premium_approved_at", sa.Column("premium_approved_at", sa.DateTime(timezone=True), nullable=True)),
    ]
    for name, col in session_cols:
        if not _has_column("personality_test_sessions", name):
            op.add_column("personality_test_sessions", col)

    bind = op.get_bind()
    if _has_column("personality_test_sessions", "telegram_user_id"):
        if bind.dialect.name == "postgresql":
            op.execute(
                """
                ALTER TABLE personality_test_sessions
                ALTER COLUMN telegram_user_id TYPE BIGINT
                USING NULLIF(regexp_replace(telegram_user_id, '[^0-9]', '', 'g'), '')::bigint
                """
            )
        elif bind.dialect.name == "sqlite":
            with op.batch_alter_table("personality_test_sessions") as batch_op:
                batch_op.alter_column(
                    "telegram_user_id",
                    type_=sa.BigInteger(),
                    existing_type=sa.String(length=64),
                    existing_nullable=True,
                )

    if not _has_table("payment_requests"):
        op.create_table(
            "payment_requests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
            sa.Column("telegram_username", sa.String(length=64), nullable=True),
            sa.Column("telegram_first_name", sa.String(length=128), nullable=True),
            sa.Column("amount", sa.Integer(), nullable=False, server_default="9999"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("receipt_file_id", sa.String(length=256), nullable=True),
            sa.Column("receipt_type", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("receipt_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.String(length=128), nullable=True),
            sa.ForeignKeyConstraint(["session_id"], ["personality_test_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_payment_requests_session_id", "payment_requests", ["session_id"], unique=False)
        op.create_index("ix_payment_requests_telegram_user_id", "payment_requests", ["telegram_user_id"], unique=False)
        op.create_index("ix_payment_requests_status", "payment_requests", ["status"], unique=False)


def downgrade() -> None:
    if _has_table("payment_requests"):
        op.drop_index("ix_payment_requests_status", table_name="payment_requests")
        op.drop_index("ix_payment_requests_telegram_user_id", table_name="payment_requests")
        op.drop_index("ix_payment_requests_session_id", table_name="payment_requests")
        op.drop_table("payment_requests")
    for name in ("premium_approved_at", "premium_requested_at", "telegram_first_name", "telegram_username"):
        if _has_column("personality_test_sessions", name):
            op.drop_column("personality_test_sessions", name)

"""Telegram users, referrals, session telegram fields

Revision ID: 019_telegram_users
Revises: 018_session_intent_feedback
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "019_telegram_users"
down_revision: Union[str, None] = "018_session_intent_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSIONS = "personality_test_sessions"
SESSION_COLUMNS = (
    ("telegram_last_name", sa.String(length=128)),
    ("premium_source", sa.String(length=32)),
)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _has_table("telegram_users"):
        op.create_table(
            "telegram_users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("telegram_username", sa.String(length=64), nullable=True),
            sa.Column("telegram_first_name", sa.String(length=128), nullable=True),
            sa.Column("telegram_last_name", sa.String(length=128), nullable=True),
            sa.Column("phone_number", sa.String(length=32), nullable=True),
            sa.Column("bot_started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("phone_shared_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("premium_source", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("telegram_id"),
        )
        op.create_index("ix_telegram_users_telegram_id", "telegram_users", ["telegram_id"], unique=True)

    if not _has_table("telegram_referrals"):
        op.create_table(
            "telegram_referrals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("referrer_telegram_user_id", sa.Integer(), nullable=False),
            sa.Column("referred_telegram_user_id", sa.Integer(), nullable=False),
            sa.Column("referred_session_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["referrer_telegram_user_id"], ["telegram_users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["referred_telegram_user_id"], ["telegram_users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["referred_session_id"], ["personality_test_sessions.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("referred_telegram_user_id"),
        )
        op.create_index(
            "ix_telegram_referrals_referrer",
            "telegram_referrals",
            ["referrer_telegram_user_id"],
            unique=False,
        )

    for name, col_type in SESSION_COLUMNS:
        if not _has_column(SESSIONS, name):
            op.add_column(SESSIONS, sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(SESSION_COLUMNS):
        if _has_column(SESSIONS, name):
            op.drop_column(SESSIONS, name)
    if _has_table("telegram_referrals"):
        op.drop_index("ix_telegram_referrals_referrer", table_name="telegram_referrals")
        op.drop_table("telegram_referrals")
    if _has_table("telegram_users"):
        op.drop_index("ix_telegram_users_telegram_id", table_name="telegram_users")
        op.drop_table("telegram_users")

"""Ko'p admin va audit jurnali: admin_users va admin_audit_log

Revision ID: 013_admins
Revises: 012_variants

Bu migratsiya ATAYLAB hech qanday hisob yaratmaydi: bootstrap ilova kodida bajariladi
(app/services/admin_service.py). Migratsiya `app.config` ni o'qisa, alembic ni bo'sh
muhitda ishga tushirish (CI, konteyner) sozlama tekshiruvlariga taqalib qolardi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "013_admins"
down_revision: Union[str, None] = "012_variants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USERS = "admin_users"
AUDIT = "admin_audit_log"
ROLE_CHECK = "ck_admin_users_role"
ROLE_VALUES = ("owner", "moderator", "viewer")


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _role_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in ROLE_VALUES)
    return f"role IN ({values})"


def upgrade() -> None:
    if not _has_table(USERS):
        op.create_table(
            USERS,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("username", sa.String(length=64), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=16), nullable=False, server_default="moderator"),
            sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(_role_check_sql(), name=ROLE_CHECK),
        )
        op.create_index("ix_admin_users_username", USERS, ["username"], unique=True)
        op.create_index("ix_admin_users_telegram_user_id", USERS, ["telegram_user_id"], unique=True)

    if not _has_table(AUDIT):
        op.create_table(
            AUDIT,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("actor_type", sa.String(length=16), nullable=False),
            sa.Column("actor_label", sa.String(length=64), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=48), nullable=False),
            sa.Column("target_type", sa.String(length=32), nullable=True),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("detail", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_admin_audit_log_action", AUDIT, ["action"])
        op.create_index("ix_admin_audit_log_created_at", AUDIT, ["created_at"])


def downgrade() -> None:
    if _has_table(AUDIT):
        op.drop_table(AUDIT)
    if _has_table(USERS):
        op.drop_table(USERS)

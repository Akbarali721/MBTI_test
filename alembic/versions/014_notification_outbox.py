"""Bildirishnoma navbati: notification_outbox va service_heartbeat

Revision ID: 014_outbox
Revises: 013_admins

`notification_outbox` da `payment_requests` ga FK ATAYLAB yo'q: CASCADE yuborilmagan
xabarni jimgina o'chirib yuborardi, RESTRICT esa saqlash siyosatini bloklardi. Ishchi
nishon qatorini topa olmasa, qatorni "cancelled" qiladi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "014_outbox"
down_revision: Union[str, None] = "013_admins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OUTBOX = "notification_outbox"
HEARTBEAT = "service_heartbeat"
STATUS_CHECK = "ck_notification_outbox_status"
DUE_INDEX = "ix_notification_outbox_due"
STATUS_VALUES = ("pending", "sending", "sent", "cancelled", "blocked", "failed", "invalid")


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _status_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in STATUS_VALUES)
    return f"status IN ({values})"


def upgrade() -> None:
    if not _has_table(OUTBOX):
        op.create_table(
            OUTBOX,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("kind", sa.String(length=32), nullable=False),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("params", sa.JSON(), nullable=False),
            sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="8"),
            sa.Column("dedup_key", sa.String(length=160), nullable=False),
            sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("claimed_by", sa.String(length=64), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(_status_check_sql(), name=STATUS_CHECK),
        )
        op.create_index("ix_notification_outbox_kind", OUTBOX, ["kind"])
        op.create_index("ix_notification_outbox_status", OUTBOX, ["status"])
        op.create_index("ix_notification_outbox_dedup_key", OUTBOX, ["dedup_key"], unique=True)
        op.create_index(DUE_INDEX, OUTBOX, ["status", "next_attempt_at"])

    if not _has_table(HEARTBEAT):
        op.create_table(
            HEARTBEAT,
            sa.Column("name", sa.String(length=32), nullable=False),
            sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("detail", sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint("name"),
        )


def downgrade() -> None:
    if _has_table(HEARTBEAT):
        op.drop_table(HEARTBEAT)
    if _has_table(OUTBOX):
        op.drop_table(OUTBOX)

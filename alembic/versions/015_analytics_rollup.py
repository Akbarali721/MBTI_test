"""Voronka va saqlash siyosati: session_daily_stats, anonymized_at, created_at indeksi

Revision ID: 015_rollup
Revises: 014_outbox

Uchta ish:
1. `session_daily_stats` — kunlik agregat. Saqlash siyosati eskirgan sessiyalarni
   o'chirganda voronka denominatorlari shu jadvalda qoladi.
2. `personality_test_sessions.anonymized_at` — anonimlashtirilgan qatorni belgilash.
3. `started_at` ni to'ldirish: 003 migratsiyasi ustunni backfill'siz qo'shgan, shuning
   uchun eski tugallangan sessiyalarda u NULL va voronka "tugatgan > boshlagan"
   ko'rinishida chiqardi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "015_rollup"
down_revision: Union[str, None] = "014_outbox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSIONS = "personality_test_sessions"
ROLLUP = "session_daily_stats"
CREATED_INDEX = "ix_personality_test_sessions_created_at"


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(col["name"] == name for col in inspect(op.get_bind()).get_columns(table))


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in inspect(op.get_bind()).get_indexes(table))


def upgrade() -> None:
    if not _has_table(ROLLUP):
        op.create_table(
            ROLLUP,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("day", sa.DateTime(timezone=True), nullable=False),
            sa.Column("variant", sa.String(length=8), nullable=False, server_default="A"),
            sa.Column("visited", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("payment_started", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("receipt_sent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approved", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("day", "variant", name="uq_session_daily_stats_day_variant"),
        )
        op.create_index("ix_session_daily_stats_day", ROLLUP, ["day"])

    if _has_table(SESSIONS):
        if not _has_column(SESSIONS, "anonymized_at"):
            op.add_column(SESSIONS, sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_index(SESSIONS, CREATED_INDEX):
            # Voronka kogortasi ham, saqlash siyosati ham shu ustun bo'yicha filtrlaydi.
            op.create_index(CREATED_INDEX, SESSIONS, ["created_at"])

        op.execute(
            sa.text(
                f"UPDATE {SESSIONS} SET started_at = COALESCE(completed_at, created_at) "
                "WHERE started_at IS NULL AND status <> 'visited'"
            )
        )


def downgrade() -> None:
    if _has_table(SESSIONS):
        if _has_index(SESSIONS, CREATED_INDEX):
            op.drop_index(CREATED_INDEX, table_name=SESSIONS)
        if _has_column(SESSIONS, "anonymized_at"):
            with op.batch_alter_table(SESSIONS) as batch:
                batch.drop_column("anonymized_at")
    if _has_table(ROLLUP):
        op.drop_table(ROLLUP)

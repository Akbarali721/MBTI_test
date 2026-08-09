"""Referal mukofoti va AI maslahatlar

Revision ID: 016_referral_ai
Revises: 015_rollup

Ikkita mahsulot imkoniyati:

1. Referal. Sessiyaga uch ustun qo'shiladi: `premium_until` (mukofot bergan vaqtli
   premium), `referred_by_session_id` (kimning havolasi orqali kelgan) va
   `referral_milestones_granted` (necha marta mukofot berilgan).

   `referred_by_session_id` — o'ziga havola qiluvchi FK, ON DELETE SET NULL bilan.
   CASCADE bo'lsa taklif qilgan sessiyani o'chirish taklif qilinganlarni ham olib
   ketardi; RESTRICT bo'lsa saqlash siyosati eski qatorni o'chira olmasdi.

   SQLite'da mavjud jadvalga FK qo'shish uchun jadvalni qayta yozish kerak
   (batch_alter_table). Buni ATAYLAB qilmaymiz: bu yerda FK faqat ma'lumot
   butunligining qo'shimcha qatlami, mantiq esa xizmat qatlamida — jadvalni qayta
   yozish esa Postgresʼda keraksiz va SQLite'da xatarli. Postgresʼda FK qo'shiladi,
   SQLiteʼda ustun FKʼsiz qoladi.

2. `ai_advice_reports` — AI yaratgan 5 ta maslahat. Yozuvda muvaffaqiyatsizlik ham
   saqlanadi (status='failed'), aks holda tugma har bosilganda pullik API chaqirilardi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "016_referral_ai"
down_revision: Union[str, None] = "015_rollup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSIONS = "personality_test_sessions"
ADVICE = "ai_advice_reports"
REFERRER_INDEX = "ix_personality_test_sessions_referred_by_session_id"
REFERRER_FK = "fk_personality_test_sessions_referred_by"
ADVICE_SESSION_INDEX = "ix_ai_advice_reports_session_id"

NEW_SESSION_COLUMNS = ("premium_until", "referred_by_session_id", "referral_milestones_granted")


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(col["name"] == name for col in inspect(op.get_bind()).get_columns(table))


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in inspect(op.get_bind()).get_indexes(table))


def upgrade() -> None:
    if _has_table(SESSIONS):
        if not _has_column(SESSIONS, "premium_until"):
            op.add_column(SESSIONS, sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True))
        if not _has_column(SESSIONS, "referred_by_session_id"):
            op.add_column(SESSIONS, sa.Column("referred_by_session_id", sa.Integer(), nullable=True))
            if not _has_index(SESSIONS, REFERRER_INDEX):
                # Har tugatishda "shu sessiyaga nechta taklif bor" so'raladi.
                op.create_index(REFERRER_INDEX, SESSIONS, ["referred_by_session_id"])
            if op.get_bind().dialect.name == "postgresql":
                op.create_foreign_key(
                    REFERRER_FK,
                    SESSIONS,
                    SESSIONS,
                    ["referred_by_session_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
        if not _has_column(SESSIONS, "referral_milestones_granted"):
            op.add_column(
                SESSIONS,
                sa.Column(
                    "referral_milestones_granted",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                ),
            )

    if not _has_table(ADVICE):
        op.create_table(
            ADVICE,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("language", sa.String(length=5), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("model", sa.String(length=64), nullable=False),
            sa.Column("prompt_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("items", sa.JSON(), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("input_tokens", sa.Integer(), nullable=True),
            sa.Column("output_tokens", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], [f"{SESSIONS}.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "language", name="uq_ai_advice_session_language"),
            sa.CheckConstraint("status IN ('ready', 'failed')", name="ck_ai_advice_reports_status"),
        )
        op.create_index(ADVICE_SESSION_INDEX, ADVICE, ["session_id"])


def downgrade() -> None:
    if _has_table(ADVICE):
        op.drop_table(ADVICE)

    if not _has_table(SESSIONS):
        return
    if op.get_bind().dialect.name == "postgresql" and _has_column(SESSIONS, "referred_by_session_id"):
        op.drop_constraint(REFERRER_FK, SESSIONS, type_="foreignkey")
    if _has_index(SESSIONS, REFERRER_INDEX):
        op.drop_index(REFERRER_INDEX, table_name=SESSIONS)
    # Uchta ustun bitta batch ichida: SQLite har drop_column uchun jadvalni qayta
    # yozadi, ya'ni alohida-alohida qilinsa uch marta ko'chirish bo'lardi.
    existing = [name for name in NEW_SESSION_COLUMNS if _has_column(SESSIONS, name)]
    if existing:
        with op.batch_alter_table(SESSIONS) as batch:
            for name in existing:
                batch.drop_column(name)

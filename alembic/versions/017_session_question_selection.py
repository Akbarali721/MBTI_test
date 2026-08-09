"""Per-session stratified question selection (48-bank -> 24).

Revision ID: 017_session_questions
Revises: 016_referral_ai
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "017_session_questions"
down_revision: str | None = "016_referral_ai"
branch_labels = None
depends_on = None

SESSION_QUESTIONS = "personality_session_questions"
QUESTIONS = "personality_questions"
SESSIONS = "personality_test_sessions"


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    if not _has_table(table):
        return False
    return column in {col["name"] for col in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column(QUESTIONS, "primary_pole"):
        op.add_column(QUESTIONS, sa.Column("primary_pole", sa.String(length=1), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE personality_questions SET primary_pole = CASE dimension
                    WHEN 'EI' THEN 'e'
                    WHEN 'SN' THEN 's'
                    WHEN 'TF' THEN 't'
                    WHEN 'JP' THEN 'j'
                END
                WHERE primary_pole IS NULL
                """
            )
        )
        with op.batch_alter_table(QUESTIONS) as batch:
            batch.alter_column("primary_pole", nullable=False)

    if not _has_table(SESSION_QUESTIONS):
        op.create_table(
            SESSION_QUESTIONS,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], [f"{QUESTIONS}.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["session_id"], [f"{SESSIONS}.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "question_id", name="uq_session_question_once"),
            sa.UniqueConstraint("session_id", "display_order", name="uq_session_question_order"),
        )
        op.create_index(
            "ix_personality_session_questions_session_id",
            SESSION_QUESTIONS,
            ["session_id"],
        )

    for col in ("ei_low_confidence", "sn_low_confidence", "tf_low_confidence", "jp_low_confidence"):
        if not _has_column(SESSIONS, col):
            op.add_column(
                SESSIONS,
                sa.Column(col, sa.Boolean(), server_default=sa.text("0"), nullable=False),
            )


def downgrade() -> None:
    for col in ("jp_low_confidence", "tf_low_confidence", "sn_low_confidence", "ei_low_confidence"):
        if _has_column(SESSIONS, col):
            op.drop_column(SESSIONS, col)
    if _has_table(SESSION_QUESTIONS):
        op.drop_index("ix_personality_session_questions_session_id", table_name=SESSION_QUESTIONS)
        op.drop_table(SESSION_QUESTIONS)
    if _has_column(QUESTIONS, "primary_pole"):
        op.drop_column(QUESTIONS, "primary_pole")

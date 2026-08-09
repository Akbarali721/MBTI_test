"""Personality test tables

Revision ID: 001_personality
Revises:
Create Date: 2026-07-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "001_personality"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return index_name in {ix["name"] for ix in inspect(op.get_bind()).get_indexes(table_name)}


def _create_index(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _session_status_enum(*, create_type: bool):
    values = ("visited", "started", "in_progress", "completed")
    name = "personality_session_status"
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.ENUM(*values, name=name, create_type=create_type)
    return sa.Enum(*values, name=name)


def _personality_dimension_enum(*, create_type: bool):
    values = ("EI", "SN", "TF", "JP")
    name = "personality_dimension"
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.ENUM(*values, name=name, create_type=create_type)
    return sa.Enum(*values, name=name)


def upgrade() -> None:
    bind = op.get_bind()
    # PostgreSQL: create types once explicitly; columns use create_type=False so
    # create_table/add_column does not emit a second CREATE TYPE (DuplicateObject).
    personality_session_status = _session_status_enum(create_type=False)
    personality_dimension = _personality_dimension_enum(create_type=False)
    if bind.dialect.name == "postgresql":
        personality_session_status.create(bind, checkfirst=True)
        personality_dimension.create(bind, checkfirst=True)

    if not _has_table("personality_test_sessions"):
        op.create_table(
            "personality_test_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("telegram_user_id", sa.String(length=64), nullable=True),
            sa.Column("token", sa.String(length=64), nullable=False),
            sa.Column("status", personality_session_status, nullable=False),
            sa.Column("current_question_index", sa.Integer(), nullable=False),
            sa.Column("result_type", sa.String(length=4), nullable=True),
            sa.Column("e_score", sa.Integer(), nullable=False),
            sa.Column("i_score", sa.Integer(), nullable=False),
            sa.Column("s_score", sa.Integer(), nullable=False),
            sa.Column("n_score", sa.Integer(), nullable=False),
            sa.Column("t_score", sa.Integer(), nullable=False),
            sa.Column("f_score", sa.Integer(), nullable=False),
            sa.Column("j_score", sa.Integer(), nullable=False),
            sa.Column("p_score", sa.Integer(), nullable=False),
            sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("premium_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )
    _create_index("ix_personality_test_sessions_token", "personality_test_sessions", ["token"])
    _create_index("ix_personality_test_sessions_user_id", "personality_test_sessions", ["user_id"])
    _create_index(
        "ix_personality_test_sessions_telegram_user_id", "personality_test_sessions", ["telegram_user_id"]
    )

    if not _has_table("personality_questions"):
        op.create_table(
            "personality_questions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("dimension", personality_dimension, nullable=False),
            sa.Column("order_number", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("order_number"),
        )

    if not _has_table("personality_options"):
        op.create_table(
            "personality_options",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("e_score", sa.Integer(), nullable=False),
            sa.Column("i_score", sa.Integer(), nullable=False),
            sa.Column("s_score", sa.Integer(), nullable=False),
            sa.Column("n_score", sa.Integer(), nullable=False),
            sa.Column("t_score", sa.Integer(), nullable=False),
            sa.Column("f_score", sa.Integer(), nullable=False),
            sa.Column("j_score", sa.Integer(), nullable=False),
            sa.Column("p_score", sa.Integer(), nullable=False),
            sa.Column("order_number", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["personality_questions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("personality_answers"):
        op.create_table(
            "personality_answers",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("option_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["option_id"], ["personality_options.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["question_id"], ["personality_questions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["session_id"], ["personality_test_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "question_id", name="uq_personality_answer_session_question"),
        )
    _create_index("ix_personality_answers_session_id", "personality_answers", ["session_id"])

    if not _has_table("personality_result_contents"):
        op.create_table(
            "personality_result_contents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("personality_type", sa.String(length=4), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("short_description", sa.Text(), nullable=False),
            sa.Column("free_strengths", sa.Text(), nullable=False),
            sa.Column("free_challenges", sa.Text(), nullable=False),
            sa.Column("public_view", sa.Text(), nullable=False),
            sa.Column("motivation_analysis", sa.Text(), nullable=False),
            sa.Column("work_style", sa.Text(), nullable=False),
            sa.Column("career_environment", sa.Text(), nullable=False),
            sa.Column("friendship_style", sa.Text(), nullable=False),
            sa.Column("relationship_needs", sa.Text(), nullable=False),
            sa.Column("compatible_people", sa.Text(), nullable=False),
            sa.Column("difficult_communication", sa.Text(), nullable=False),
            sa.Column("action_plan", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("personality_type"),
        )
    _create_index(
        "ix_personality_result_contents_personality_type", "personality_result_contents", ["personality_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_personality_result_contents_personality_type", table_name="personality_result_contents")
    op.drop_table("personality_result_contents")
    op.drop_index("ix_personality_answers_session_id", table_name="personality_answers")
    op.drop_table("personality_answers")
    op.drop_table("personality_options")
    op.drop_table("personality_questions")
    op.drop_index("ix_personality_test_sessions_telegram_user_id", table_name="personality_test_sessions")
    op.drop_index("ix_personality_test_sessions_user_id", table_name="personality_test_sessions")
    op.drop_index("ix_personality_test_sessions_token", table_name="personality_test_sessions")
    op.drop_table("personality_test_sessions")
    sa.Enum(name="personality_dimension").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="personality_session_status").drop(op.get_bind(), checkfirst=True)

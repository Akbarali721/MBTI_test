"""Session analytics fields and visited status support

Revision ID: 003_session_analytics
Revises: 002_appearance_theme
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "003_session_analytics"
down_revision: Union[str, None] = "002_appearance_theme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE personality_session_status ADD VALUE IF NOT EXISTS 'visited'")

    columns = [
        ("total_questions", sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0")),
        ("answered_questions", sa.Column("answered_questions", sa.Integer(), nullable=False, server_default="0")),
        ("source", sa.Column("source", sa.String(length=64), nullable=True)),
        ("started_at", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)),
        ("last_activity_at", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True)),
    ]
    for name, col in columns:
        if not _has_column("personality_test_sessions", name):
            op.add_column("personality_test_sessions", col)

    if _has_column("personality_test_sessions", "source"):
        op.create_index(
            "ix_personality_test_sessions_source",
            "personality_test_sessions",
            ["source"],
            unique=False,
            if_not_exists=True,
        )


def downgrade() -> None:
    if _has_column("personality_test_sessions", "source"):
        op.drop_index("ix_personality_test_sessions_source", table_name="personality_test_sessions")
    for name in ("last_activity_at", "started_at", "source", "answered_questions", "total_questions"):
        if _has_column("personality_test_sessions", name):
            op.drop_column("personality_test_sessions", name)

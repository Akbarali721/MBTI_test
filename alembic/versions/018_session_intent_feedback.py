"""Session intent and result feedback fields

Revision ID: 018_session_intent_feedback
Revises: 017_session_questions
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "018_session_intent_feedback"
down_revision: Union[str, None] = "017_session_questions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_test_sessions"
COLUMNS = (
    ("intent", sa.String(length=32)),
    ("feedback_rating", sa.String(length=32)),
    ("feedback_interest", sa.String(length=32)),
)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    for name, col_type in COLUMNS:
        if not _has_column(TABLE, name):
            op.add_column(TABLE, sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(COLUMNS):
        if _has_column(TABLE, name):
            op.drop_column(TABLE, name)

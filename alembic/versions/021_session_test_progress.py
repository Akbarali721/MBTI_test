"""Session test progress tracking

Revision ID: 021_session_test_progress
Revises: 020_telegram_user_last_seen
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "021_session_test_progress"
down_revision: Union[str, None] = "020_telegram_user_last_seen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_test_sessions"
COLUMNS = (
    ("max_question_reached", sa.Integer(), False, "0"),
    ("current_question_number", sa.Integer(), False, "0"),
    ("last_answered_at", sa.DateTime(timezone=True), True, None),
)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    for name, col_type, nullable, server_default in COLUMNS:
        if not _has_column(TABLE, name):
            kwargs: dict = {"nullable": nullable}
            if server_default is not None:
                kwargs["server_default"] = server_default
            op.add_column(TABLE, sa.Column(name, col_type, **kwargs))

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            text(
                f"""
                UPDATE {TABLE}
                SET max_question_reached = CASE
                    WHEN status = 'completed' THEN GREATEST(COALESCE(NULLIF(total_questions, 0), 24), 1)
                    ELSE GREATEST(
                        COALESCE(current_question_index, 0),
                        COALESCE(answered_questions, 0),
                        CASE WHEN started_at IS NOT NULL THEN 1 ELSE 0 END
                    )
                END,
                current_question_number = CASE
                    WHEN status = 'completed' THEN GREATEST(COALESCE(NULLIF(total_questions, 0), 24), 1)
                    WHEN current_question_index > 0 THEN current_question_index
                    WHEN answered_questions > 0 THEN answered_questions
                    WHEN started_at IS NOT NULL THEN 1
                    ELSE 0
                END
                WHERE COALESCE(max_question_reached, 0) = 0
                """
            )
        )
    else:
        op.execute(
            text(
                f"""
                UPDATE {TABLE}
                SET max_question_reached = CASE
                    WHEN status = 'completed' THEN MAX(COALESCE(NULLIF(total_questions, 0), 24), 1)
                    ELSE MAX(
                        COALESCE(current_question_index, 0),
                        COALESCE(answered_questions, 0),
                        CASE WHEN started_at IS NOT NULL THEN 1 ELSE 0 END
                    )
                END,
                current_question_number = CASE
                    WHEN status = 'completed' THEN MAX(COALESCE(NULLIF(total_questions, 0), 24), 1)
                    WHEN current_question_index > 0 THEN current_question_index
                    WHEN answered_questions > 0 THEN answered_questions
                    WHEN started_at IS NOT NULL THEN 1
                    ELSE 0
                END
                WHERE COALESCE(max_question_reached, 0) = 0
                """
            )
        )


def downgrade() -> None:
    for name, _, _, _ in reversed(COLUMNS):
        if _has_column(TABLE, name):
            op.drop_column(TABLE, name)

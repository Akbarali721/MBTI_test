"""Natija bo‘yicha foydalanuvchi fikri (rating + comment)

Revision ID: 022_result_user_feedback
Revises: 021_session_test_progress
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_result_user_feedback"
down_revision: Union[str, None] = "021_session_test_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_result_user_feedback"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["personality_test_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["telegram_user_id"],
            ["telegram_users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_result_user_feedback_session"),
    )
    op.create_index("ix_result_user_feedback_session_id", TABLE, ["session_id"], unique=False)
    op.create_index("ix_result_user_feedback_created_at", TABLE, ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_result_user_feedback_created_at", table_name=TABLE)
    op.drop_index("ix_result_user_feedback_session_id", table_name=TABLE)
    op.drop_table(TABLE)

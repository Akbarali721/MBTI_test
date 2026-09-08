"""Telegram user last_seen_at

Revision ID: 020_telegram_user_last_seen
Revises: 019_telegram_users
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "020_telegram_user_last_seen"
down_revision: Union[str, None] = "019_telegram_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "telegram_users"
COLUMN = "last_seen_at"


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    if not _has_column(TABLE, COLUMN):
        op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _has_column(TABLE, COLUMN):
        op.drop_column(TABLE, COLUMN)

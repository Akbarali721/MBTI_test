"""personality_test_sessions: ommaviy ulashish kodi

Revision ID: 010_share_code
Revises: 009_active_payment
"""

import secrets
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "010_share_code"
down_revision: Union[str, None] = "009_active_payment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_test_sessions"
COLUMN = "share_code"
INDEX_NAME = "ix_personality_test_sessions_share_code"


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_column(table_name: str, name: str) -> bool:
    return any(col["name"] == name for col in inspect(op.get_bind()).get_columns(table_name))


def _has_index(table_name: str, name: str) -> bool:
    return any(ix["name"] == name for ix in inspect(op.get_bind()).get_indexes(table_name))


def _backfill() -> None:
    """Mavjud qatorlarga noyob kod beriladi — ulashish havolasi ular uchun ham ishlasin."""
    bind = op.get_bind()
    table = sa.table(TABLE, sa.column("id", sa.Integer), sa.column(COLUMN, sa.String))
    ids = [row[0] for row in bind.execute(sa.select(table.c.id).where(table.c.share_code.is_(None)))]
    used: set[str] = {
        row[0]
        for row in bind.execute(sa.select(table.c.share_code).where(table.c.share_code.is_not(None)))
    }
    for row_id in ids:
        code = secrets.token_urlsafe(8)
        while code in used:
            code = secrets.token_urlsafe(8)
        used.add(code)
        bind.execute(sa.update(table).where(table.c.id == row_id).values(share_code=code))


def upgrade() -> None:
    if not _has_table(TABLE) or _has_column(TABLE, COLUMN):
        return
    op.add_column(TABLE, sa.Column(COLUMN, sa.String(length=24), nullable=True))
    _backfill()
    if not _has_index(TABLE, INDEX_NAME):
        op.create_index(INDEX_NAME, TABLE, [COLUMN], unique=True)


def downgrade() -> None:
    if not _has_table(TABLE) or not _has_column(TABLE, COLUMN):
        return
    if _has_index(TABLE, INDEX_NAME):
        op.drop_index(INDEX_NAME, table_name=TABLE)
    op.drop_column(TABLE, COLUMN)

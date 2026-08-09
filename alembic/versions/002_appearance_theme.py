"""Add appearance_theme to personality sessions

Revision ID: 002_appearance_theme
Revises: 001_personality
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "002_appearance_theme"
down_revision: Union[str, None] = "001_personality"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {col["name"] for col in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    if _has_column("personality_test_sessions", "appearance_theme"):
        return

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite: store enum values as text (matches SQLAlchemy Enum on SQLite).
        op.add_column(
            "personality_test_sessions",
            sa.Column("appearance_theme", sa.String(length=20), nullable=True),
        )
        return

    appearance_theme = postgresql.ENUM(
        "male",
        "female",
        "neutral",
        name="appearance_theme",
        create_type=False,
    )
    appearance_theme.create(bind, checkfirst=True)
    op.add_column(
        "personality_test_sessions",
        sa.Column("appearance_theme", appearance_theme, nullable=True),
    )


def downgrade() -> None:
    if not _has_column("personality_test_sessions", "appearance_theme"):
        return

    op.drop_column("personality_test_sessions", "appearance_theme")
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        sa.Enum(name="appearance_theme").drop(bind, checkfirst=True)

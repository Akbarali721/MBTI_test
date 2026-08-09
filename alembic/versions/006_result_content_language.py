"""Language column for personality result contents

Revision ID: 006_result_language
Revises: 005_payment_code
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "006_result_language"
down_revision: Union[str, None] = "005_payment_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "personality_result_contents"
TMP_TABLE = "personality_result_contents_tmp_006"
UNIQUE_NAME = "uq_result_content_type_language"
INDEX = "ix_personality_result_contents_personality_type"
DEFAULT_LANGUAGE = "uz"

TEXT_COLUMNS = (
    "short_description",
    "free_strengths",
    "free_challenges",
    "public_view",
    "motivation_analysis",
    "work_style",
    "career_environment",
    "friendship_style",
    "relationship_needs",
    "compatible_people",
    "difficult_communication",
    "action_plan",
)

COPY_COLUMNS = ("id", "personality_type", "title", *TEXT_COLUMNS, "is_active")


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspect(op.get_bind()).get_columns(table_name)}


def _has_constraint(table_name: str, constraint_name: str) -> bool:
    inspector = inspect(op.get_bind())
    names = {uq["name"] for uq in inspector.get_unique_constraints(table_name)}
    names |= {ix["name"] for ix in inspector.get_indexes(table_name)}
    return constraint_name in names


def _new_table_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("personality_type", sa.String(length=4), nullable=False),
        sa.Column(
            "language",
            sa.String(length=5),
            nullable=False,
            server_default=DEFAULT_LANGUAGE,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        *[sa.Column(name, sa.Text(), nullable=False) for name in TEXT_COLUMNS],
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("personality_type", "language", name=UNIQUE_NAME),
    ]


def _upgrade_sqlite() -> None:
    # SQLite'da nomsiz UNIQUE(personality_type) cheklovini olib tashlash uchun jadval qayta quriladi.
    op.create_table(TMP_TABLE, *_new_table_columns())
    columns = ", ".join(COPY_COLUMNS)
    op.execute(
        sa.text(
            f"INSERT INTO {TMP_TABLE} ({columns}, language) "
            f"SELECT {columns}, '{DEFAULT_LANGUAGE}' FROM {TABLE}"
        )
    )
    op.drop_table(TABLE)
    op.rename_table(TMP_TABLE, TABLE)
    op.create_index(INDEX, TABLE, ["personality_type"])


def _upgrade_generic() -> None:
    if not _has_column(TABLE, "language"):
        op.add_column(
            TABLE,
            sa.Column(
                "language",
                sa.String(length=5),
                nullable=False,
                server_default=DEFAULT_LANGUAGE,
            ),
        )
    op.execute(sa.text(f"UPDATE {TABLE} SET language = '{DEFAULT_LANGUAGE}' WHERE language IS NULL"))
    # create_all bilan qurilgan bazada cheklov nomi Postgres standarti bo'yicha yaraladi.
    for legacy_name in (
        f"{TABLE}_personality_type_key",
        "uq_personality_result_contents_personality_type",
    ):
        op.execute(sa.text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {legacy_name}"))
    if not _has_constraint(TABLE, UNIQUE_NAME):
        op.create_unique_constraint(UNIQUE_NAME, TABLE, ["personality_type", "language"])


def upgrade() -> None:
    if _has_column(TABLE, "language"):
        return
    if op.get_bind().dialect.name == "sqlite":
        _upgrade_sqlite()
    else:
        _upgrade_generic()


def downgrade() -> None:
    if not _has_column(TABLE, "language"):
        return
    bind = op.get_bind()
    op.execute(sa.text(f"DELETE FROM {TABLE} WHERE language <> '{DEFAULT_LANGUAGE}'"))
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(TABLE) as batch_op:
            batch_op.drop_constraint(UNIQUE_NAME, type_="unique")
            batch_op.drop_column("language")
        return
    op.drop_constraint(UNIQUE_NAME, TABLE, type_="unique")
    op.drop_column(TABLE, "language")
    op.create_unique_constraint(f"{TABLE}_personality_type_key", TABLE, ["personality_type"])

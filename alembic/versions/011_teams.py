"""Jamoa / HR rejimi: teams va team_members jadvallari

Revision ID: 011_teams
Revises: 010_share_code
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "011_teams"
down_revision: Union[str, None] = "010_share_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TEAMS = "teams"
MEMBERS = "team_members"


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _has_table(TEAMS):
        op.create_table(
            TEAMS,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("invite_code", sa.String(length=24), nullable=False),
            sa.Column("manage_code", sa.String(length=24), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_teams_invite_code", TEAMS, ["invite_code"], unique=True)
        op.create_index("ix_teams_manage_code", TEAMS, ["manage_code"], unique=True)

    if not _has_table(MEMBERS):
        op.create_table(
            MEMBERS,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("team_id", sa.Integer(), nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("display_name", sa.String(length=80), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["session_id"], ["personality_test_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("team_id", "session_id", name="uq_team_members_team_session"),
        )
        op.create_index("ix_team_members_team_id", MEMBERS, ["team_id"])
        op.create_index("ix_team_members_session_id", MEMBERS, ["session_id"])


def downgrade() -> None:
    if _has_table(MEMBERS):
        op.drop_table(MEMBERS)
    if _has_table(TEAMS):
        op.drop_table(TEAMS)

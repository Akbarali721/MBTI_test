"""Migratsiya zanjiri boʻsh bazada oxirigacha ishlashi kerak.

Alembic alohida jarayonda ishga tushiriladi: ilova import qilgan enginega ham,
testlar yaratgan sxemaga ham tegmaydi.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "personality_test_sessions",
    "personality_questions",
    "personality_options",
    "personality_answers",
    "personality_result_contents",
    "payment_requests",
}


def _run_alembic(args: list[str], database_url: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "DATABASE_URL": database_url,
        "SECRET_KEY": "migratsiya-testi-uchun-kalit-" + "z" * 24,
        "DEBUG": "true",
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def _table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _column_names(database_url: str, table: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return {column["name"] for column in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()


@pytest.mark.slow
def test_upgrade_head_builds_the_whole_schema(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'upgrade.db').as_posix()}"

    result = _run_alembic(["upgrade", "head"], database_url)
    assert result.returncode == 0, result.stderr or result.stdout

    tables = _table_names(database_url)
    assert tables >= EXPECTED_TABLES, sorted(tables)

    session_columns = _column_names(database_url, "personality_test_sessions")
    # Keyingi migratsiyalar qoʻshgan ustunlar ham joyida boʻlishi kerak.
    assert {"payment_code", "appearance_theme", "source", "premium_approved_at"} <= session_columns
    assert "language" in _column_names(database_url, "personality_result_contents")


@pytest.mark.slow
def test_downgrade_base_removes_every_table(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'downgrade.db').as_posix()}"

    upgrade = _run_alembic(["upgrade", "head"], database_url)
    assert upgrade.returncode == 0, upgrade.stderr or upgrade.stdout

    downgrade = _run_alembic(["downgrade", "base"], database_url)
    assert downgrade.returncode == 0, downgrade.stderr or downgrade.stdout

    remaining = _table_names(database_url) - {"alembic_version"}
    assert remaining == set(), sorted(remaining)


@pytest.mark.slow
def test_upgrade_is_idempotent_when_run_twice(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'twice.db').as_posix()}"

    first = _run_alembic(["upgrade", "head"], database_url)
    assert first.returncode == 0, first.stderr or first.stdout
    second = _run_alembic(["upgrade", "head"], database_url)
    assert second.returncode == 0, second.stderr or second.stdout


@pytest.mark.slow
def test_migrated_schema_allows_two_question_variants(tmp_path):
    """001 migratsiyasi order_number'ni NOMSIZ unique qilgan edi.

    Model create_all bilan qurilganda bu cheklov yo'q, shuning uchun faqat
    haqiqiy migratsiya zanjiri ustida sinash bu nuqsonni ochadi.
    """
    from sqlalchemy import text

    database_url = f"sqlite:///{(tmp_path / 'variants.db').as_posix()}"
    result = _run_alembic(["upgrade", "head"], database_url)
    assert result.returncode == 0, result.stderr or result.stdout

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            for variant in ("A", "B"):
                connection.execute(
                    text(
                        "INSERT INTO personality_questions (text, dimension, order_number, is_active, variant)"
                        " VALUES (:text, 'EI', 1, 1, :variant)"
                    ),
                    {"text": f"{variant} savoli", "variant": variant},
                )
            rows = (
                connection.execute(text("SELECT variant FROM personality_questions ORDER BY variant"))
                .scalars()
                .all()
            )
    finally:
        engine.dispose()

    assert rows == ["A", "B"]


@pytest.mark.slow
def test_migrated_schema_has_the_team_tables(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'teams.db').as_posix()}"
    result = _run_alembic(["upgrade", "head"], database_url)
    assert result.returncode == 0, result.stderr or result.stdout

    tables = _table_names(database_url)
    assert {"teams", "team_members"} <= tables
    assert {"invite_code", "manage_code"} <= _column_names(database_url, "teams")
    assert "share_code" in _column_names(database_url, "personality_test_sessions")
    assert "variant" in _column_names(database_url, "personality_test_sessions")

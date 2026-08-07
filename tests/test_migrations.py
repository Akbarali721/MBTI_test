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


@pytest.mark.slow
def test_migrated_schema_has_the_operations_tables(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'ops.db').as_posix()}"
    result = _run_alembic(["upgrade", "head"], database_url)
    assert result.returncode == 0, result.stderr or result.stdout

    tables = _table_names(database_url)
    assert {
        "admin_users",
        "admin_audit_log",
        "notification_outbox",
        "service_heartbeat",
        "session_daily_stats",
    } <= tables
    assert {"role", "telegram_user_id", "is_active"} <= _column_names(database_url, "admin_users")
    assert {"dedup_key", "next_attempt_at", "lease_expires_at"} <= _column_names(
        database_url, "notification_outbox"
    )
    assert "anonymized_at" in _column_names(database_url, "personality_test_sessions")


@pytest.mark.slow
def test_migrated_outbox_enforces_its_constraints(tmp_path):
    """CHECK va noyob indeks `create_all` bilan qurilgan test bazasida ko'rinmaydi.

    Aynan shu farq avval 001 dagi nomsiz UNIQUE nuqsonini yashirgan edi.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    database_url = f"sqlite:///{(tmp_path / 'outbox.db').as_posix()}"
    assert _run_alembic(["upgrade", "head"], database_url).returncode == 0

    insert = text(
        "INSERT INTO notification_outbox"
        " (kind, chat_id, params, schema_version, status, attempts, max_attempts,"
        "  dedup_key, next_attempt_at, created_at)"
        " VALUES ('user_approved', 1, '{}', 1, :status, 0, 8, :key,"
        "         '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
    )
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(insert, {"status": "pending", "key": "bir-xil"})

        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(insert, {"status": "pending", "key": "bir-xil"})

        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(insert, {"status": "yolgon-holat", "key": "boshqa"})
    finally:
        engine.dispose()


@pytest.mark.slow
def test_the_rollup_table_keeps_one_row_per_day_and_variant(tmp_path):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    database_url = f"sqlite:///{(tmp_path / 'rollup.db').as_posix()}"
    assert _run_alembic(["upgrade", "head"], database_url).returncode == 0

    insert = text(
        "INSERT INTO session_daily_stats (day, variant, visited, updated_at)"
        " VALUES ('2026-01-01 00:00:00', 'A', 1, '2026-01-01 00:00:00')"
    )
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(insert)
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(insert)
    finally:
        engine.dispose()


@pytest.mark.slow
def test_started_at_is_backfilled_for_legacy_rows(tmp_path):
    """003 migratsiyasi ustunni backfill'siz qo'shgan edi.

    Natijada eski tugallangan sessiyalarda `started_at` NULL bo'lib, voronkada
    "tugatgan > boshlagan" ko'rinishi chiqardi.
    """
    from sqlalchemy import text

    database_url = f"sqlite:///{(tmp_path / 'backfill.db').as_posix()}"
    assert _run_alembic(["upgrade", "014_outbox"], database_url).returncode == 0

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO personality_test_sessions"
                    " (token, status, current_question_index, e_score, i_score, s_score, n_score,"
                    "  t_score, f_score, j_score, p_score, is_premium, premium_requested,"
                    "  total_questions, answered_questions, created_at, completed_at, started_at)"
                    " VALUES ('eski-token', 'completed', 24, 0,0,0,0,0,0,0,0, 0, 0, 24, 24,"
                    "         '2026-01-01 00:00:00', '2026-01-01 00:10:00', NULL)"
                )
            )
    finally:
        engine.dispose()

    assert _run_alembic(["upgrade", "head"], database_url).returncode == 0

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            started_at = connection.execute(
                text("SELECT started_at FROM personality_test_sessions WHERE token = 'eski-token'")
            ).scalar()
    finally:
        engine.dispose()
    assert started_at is not None

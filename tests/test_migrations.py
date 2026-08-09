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
from sqlalchemy.exc import IntegrityError

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
def test_upgrade_head_on_postgresql_when_configured():
    """Guards PostgreSQL CREATE TYPE duplication (001/002 enum migrations)."""
    database_url = os.environ.get("TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("Set TEST_POSTGRES_URL to run PostgreSQL migration smoke test")
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        pytest.skip("psycopg2 not installed")

    first = _run_alembic(["upgrade", "head"], database_url)
    assert first.returncode == 0, first.stderr or first.stdout
    second = _run_alembic(["upgrade", "head"], database_url)
    assert second.returncode == 0, second.stderr or second.stdout

    tables = _table_names(database_url)
    assert tables >= EXPECTED_TABLES, sorted(tables)


@pytest.mark.slow
def test_009_deduplicates_active_payments_and_idempotent_index(tmp_path):
    """009 must dedupe active rows before partial unique index; re-run must be safe."""
    from sqlalchemy import create_engine, inspect, text

    database_url = f"sqlite:///{(tmp_path / '009_active.db').as_posix()}"
    base = _run_alembic(["upgrade", "008_enum_repair"], database_url)
    assert base.returncode == 0, base.stderr or base.stdout

    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO personality_test_sessions (
                    token, status, current_question_index,
                    e_score, i_score, s_score, n_score, t_score, f_score, j_score, p_score,
                    is_premium, premium_requested, total_questions, answered_questions
                ) VALUES (
                    'pay-dup', 'visited', 0,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 24, 0
                )
                """
            )
        )
        session_id = conn.execute(text("SELECT id FROM personality_test_sessions")).scalar_one()
        for status in ("pending", "receipt_sent", "pending"):
            conn.execute(
                text(
                    """
                    INSERT INTO payment_requests (session_id, amount, status, created_at)
                    VALUES (:sid, 100, :status, '2026-01-01 00:00:00')
                    """
                ),
                {"sid": session_id, "status": status},
            )
    engine.dispose()

    first = _run_alembic(["upgrade", "009_active_payment"], database_url)
    assert first.returncode == 0, first.stderr or first.stdout
    repeat = _run_alembic(["upgrade", "009_active_payment"], database_url)
    assert repeat.returncode == 0, repeat.stderr or repeat.stdout

    engine = create_engine(database_url)
    try:
        indexes = {ix["name"] for ix in inspect(engine).get_indexes("payment_requests")}
        assert "uq_payment_requests_active_session" in indexes
        with engine.connect() as conn:
            active = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM payment_requests
                     WHERE session_id = :sid AND status IN ('pending', 'receipt_sent')
                    """
                ),
                {"sid": session_id},
            ).scalar_one()
            rejected = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM payment_requests
                     WHERE session_id = :sid AND status = 'rejected'
                    """
                ),
                {"sid": session_id},
            ).scalar_one()
        assert active == 1
        assert rejected == 2
    finally:
        engine.dispose()


@pytest.mark.slow
def test_012_variant_unique_idempotent_on_sqlite(tmp_path):
    """012 removes UNIQUE(order_number) and adds UNIQUE(variant, order_number); re-run is safe."""
    import importlib.util
    from pathlib import Path

    from sqlalchemy import create_engine, inspect

    _revision_path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "012_question_variants.py"
    _spec = importlib.util.spec_from_file_location("migration_012", _revision_path)
    assert _spec and _spec.loader
    m012 = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(m012)

    database_url = f"sqlite:///{(tmp_path / '012_variants.db').as_posix()}"
    base = _run_alembic(["upgrade", "011_teams"], database_url)
    assert base.returncode == 0, base.stderr or base.stdout

    first = _run_alembic(["upgrade", "012_variants"], database_url)
    assert first.returncode == 0, first.stderr or first.stdout
    repeat = _run_alembic(["upgrade", "012_variants"], database_url)
    assert repeat.returncode == 0, repeat.stderr or repeat.stdout

    engine = create_engine(database_url)
    try:
        insp = inspect(engine)
        variant_order = m012.find_unique_names_for_columns(
            insp.get_unique_constraints("personality_questions"),
            insp.get_indexes("personality_questions"),
            ("variant", "order_number"),
        )
        assert variant_order
        assert m012.find_unique_names_for_columns(
            insp.get_unique_constraints("personality_questions"),
            insp.get_indexes("personality_questions"),
            ("order_number",),
        ) == []
    finally:
        engine.dispose()


@pytest.mark.slow
def test_017_boolean_low_confidence_columns_idempotent(tmp_path):
    """017 must use cross-dialect Boolean defaults; re-run after partial deploy is safe."""
    from sqlalchemy import create_engine, inspect

    database_url = f"sqlite:///{(tmp_path / '017_sessions.db').as_posix()}"
    base = _run_alembic(["upgrade", "016_referral_ai"], database_url)
    assert base.returncode == 0, base.stderr or base.stdout

    first = _run_alembic(["upgrade", "017_session_questions"], database_url)
    assert first.returncode == 0, first.stderr or first.stdout
    repeat = _run_alembic(["upgrade", "017_session_questions"], database_url)
    assert repeat.returncode == 0, repeat.stderr or repeat.stdout

    engine = create_engine(database_url)
    try:
        cols = {c["name"]: c for c in inspect(engine).get_columns("personality_test_sessions")}
        for name in ("ei_low_confidence", "sn_low_confidence", "tf_low_confidence", "jp_low_confidence"):
            assert name in cols
            assert cols[name]["nullable"] is False
        assert "personality_session_questions" in inspect(engine).get_table_names()
        assert _run_alembic(["upgrade", "head"], database_url).returncode == 0
    finally:
        engine.dispose()


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
                        "INSERT INTO personality_questions (text, dimension, order_number, is_active, variant, primary_pole)"
                        " VALUES (:text, 'EI', 1, 1, :variant, 'e')"
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


@pytest.mark.slow
def test_migrated_schema_has_the_referral_and_advice_objects(tmp_path):
    from sqlalchemy import text

    database_url = f"sqlite:///{(tmp_path / 'referral.db').as_posix()}"
    result = _run_alembic(["upgrade", "head"], database_url)
    assert result.returncode == 0, result.stderr or result.stdout

    assert "ai_advice_reports" in _table_names(database_url)
    assert {
        "premium_until",
        "referred_by_session_id",
        "referral_milestones_granted",
    } <= _column_names(database_url, "personality_test_sessions")

    engine = create_engine(database_url)
    try:
        with engine.begin() as conn:
            # Eski qatorlarda hisoblagich NULL emas, 0 bo'lishi kerak: mukofot mantiqi
            # uni sonday o'qiydi va NULL bilan taqqoslash hech qachon rost bo'lmasdi.
            conn.execute(
                text(
                    "INSERT INTO personality_test_sessions (token, status, current_question_index, "
                    "e_score, i_score, s_score, n_score, t_score, f_score, j_score, p_score, "
                    "is_premium, premium_requested, total_questions, answered_questions, variant) "
                    "VALUES ('t-referal', 'completed', 0, 0,0,0,0,0,0,0,0, 0, 0, 24, 24, 'A')"
                )
            )
            granted = conn.execute(
                text(
                    "SELECT referral_milestones_granted FROM personality_test_sessions "
                    "WHERE token = 't-referal'"
                )
            ).scalar()
            assert granted == 0

            # CHECK cheklovi `create_all` bilan qurilgan test bazasida ham bor, lekin
            # migratsiya yo'lida ham borligini alohida tekshiramiz.
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        "INSERT INTO ai_advice_reports (session_id, language, status, model, "
                        "prompt_version, items, attempts, created_at, updated_at) "
                        "SELECT id, 'uz', 'nomalum', 'm', 1, '[]', 0, '2026-01-01', '2026-01-01' "
                        "FROM personality_test_sessions WHERE token = 't-referal'"
                    )
                )
    finally:
        engine.dispose()

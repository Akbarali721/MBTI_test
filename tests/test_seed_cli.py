"""`python -m app.seed` — kontent va xizmat buyruqlari.

Sxema Alembic bilan, kontent esa shu CLI bilan boshqariladi, shuning uchun uning
har bir shoxi sinaladi: takroriy yuklash, --force tasdiqlash, qayta hisoblash va tozalash.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityResultContent, PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.seed import __main__ as seed_cli
from tests.helpers import complete_session, db_session, session_by_token


@pytest.fixture()
def seed_db(client, monkeypatch):
    """CLI oʻz sessiyasini SessionLocal orqali ochadi — uni test bazasiga qaratamiz."""
    monkeypatch.setattr(seed_cli, "SessionLocal", client.testing_session_factory)
    return client


def _content_rows(db, language: str = "uz") -> int:
    stmt = (
        select(func.count())
        .select_from(PersonalityResultContent)
        .where(PersonalityResultContent.language == language)
    )
    return int(db.scalar(stmt) or 0)


def _content_count(client, language: str) -> int:
    with db_session(client) as db:
        return _content_rows(db, language)


def test_seed_is_idempotent_on_an_already_seeded_database(seed_db, client, capsys):
    assert seed_cli.main([]) == 0
    output = capsys.readouterr().out
    assert "allaqachon mavjud" in output
    assert "Variant 'A' active questions: total=48" in output
    assert _content_count(client, "uz") == 16


def test_verify_prints_counts_and_succeeds_when_bank_is_valid(seed_db, capsys):
    assert seed_cli.main(["--verify"]) == 0
    output = capsys.readouterr().out
    assert "EI: 12" in output
    assert "total=48" in output


def test_seed_fails_when_question_bank_still_invalid(seed_db, client, monkeypatch):
    from app.models.personality import PersonalityQuestion

    with db_session(client) as db:
        for row in db.scalars(select(PersonalityQuestion)).all():
            row.is_active = False
        db.commit()

    monkeypatch.setattr(seed_cli, "seed_personality_questions", lambda db, **kw: 0)

    with pytest.raises(RuntimeError, match="Question bank not ready"):
        seed_cli.main([])


def test_refuses_default_sqlite_when_debug_is_false(seed_db, monkeypatch, capsys):
    monkeypatch.setattr(seed_cli.settings, "debug", False)
    monkeypatch.setattr(seed_cli.settings, "database_url", seed_cli._DEFAULT_SQLITE_URL)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert seed_cli.main([]) == 1
    assert "Refusing to seed default SQLite" in capsys.readouterr().err


def test_seed_loads_the_russian_catalog(seed_db, client, capsys):
    assert _content_count(client, "ru") == 0

    assert seed_cli.main(["--language", "ru"]) == 0

    assert "(ru)" in capsys.readouterr().out
    assert _content_count(client, "ru") == 16


def test_force_without_yes_is_cancelled(seed_db, capsys):
    # Pytest ostida stdin tty emas, shuning uchun tasdiqlash olinmaydi.
    assert seed_cli.main(["--force"]) == 1
    assert "Bekor qilindi" in capsys.readouterr().out


def test_force_with_yes_rewrites_content_in_place(seed_db, client, capsys):
    with db_session(client) as db:
        row = db.scalar(select(PersonalityResultContent).where(PersonalityResultContent.language == "uz"))
        assert row is not None
        row.title = "vaqtinchalik"
        db.commit()
        row_id = row.id

    assert seed_cli.main(["--force", "--yes"]) == 0
    assert "yuklandi/yangilandi" in capsys.readouterr().out

    with db_session(client) as db:
        restored = db.get(PersonalityResultContent, row_id)
        assert restored is not None
        assert restored.title != "vaqtinchalik"


def test_recompute_restores_result_type(seed_db, client, capsys):
    from tests.helpers import favor_left_option_index

    token = complete_session(client, option_picker=favor_left_option_index)
    with db_session(client) as db:
        expected = session_by_token(db, token).result_type
        session = session_by_token(db, token)
        session.result_type = "XXXX"
        db.commit()

    assert seed_cli.main(["--recompute"]) == 0
    assert "qayta hisoblangan" in capsys.readouterr().out

    with db_session(client) as db:
        assert session_by_token(db, token).result_type == expected


def test_purge_visited_removes_only_stale_rows(seed_db, client, capsys):
    with db_session(client) as db:
        repo = PersonalityRepository(db)
        stale = repo.create_session(source="cli-test")
        stale.last_activity_at = datetime.now(timezone.utc) - timedelta(days=90)
        fresh_token = repo.create_session(source="cli-test").token
        db.commit()

    assert seed_cli.main(["--purge-visited", "--days", "30"]) == 0
    assert "O'chirilgan VISITED sessiyalar" in capsys.readouterr().out

    with db_session(client) as db:
        tokens = set(db.scalars(select(PersonalityTestSession.token)).all())
        assert tokens == {fresh_token}
        assert _content_rows(db) == 16, "kontent oʻchmasligi kerak"


def test_unknown_language_is_rejected_by_the_parser(seed_db):
    with pytest.raises(SystemExit) as exc:
        seed_cli.main(["--language", "xx"])
    assert exc.value.code == 2


def test_seed_rolls_back_on_failure(seed_db, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("seed yiqildi")

    monkeypatch.setattr(seed_cli, "seed_personality_questions", _boom)
    with pytest.raises(RuntimeError, match="seed yiqildi"):
        seed_cli.main([])


def test_visited_session_status_is_untouched_by_seeding(seed_db, client):
    client.get("/personality")
    assert seed_cli.main([]) == 0
    with db_session(client) as db:
        row = db.scalar(select(PersonalityTestSession))
        assert row is not None
        assert row.status == PersonalitySessionStatus.VISITED

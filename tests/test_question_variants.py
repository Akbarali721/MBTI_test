"""Savol banki va A/B test: taqsimot, izolyatsiya va hisobot."""

import random

from sqlalchemy import select

from app.config import settings
from app.models.personality import DEFAULT_VARIANT, PersonalityQuestion, PersonalityTestSession
from app.personality.variants import choose_variant, known_variants, normalize_variant, parse_spec
from app.seed.personality_placeholders import seed_personality_questions
from app.services.admin_analytics_service import AdminAnalyticsService, VariantStats
from tests.conftest import ADMIN_PASSWORD, ADMIN_USERNAME
from tests.helpers import complete_session, db_session, session_by_token

# --------------------------- taqsimot mantiqi ---------------------------


def test_parse_spec_reads_weights():
    assert parse_spec("A:70,B:30") == [("A", 70), ("B", 30)]
    assert parse_spec("A") == [("A", 1)]
    assert parse_spec("a:1, b:2 ") == [("A", 1), ("B", 2)]


def test_parse_spec_falls_back_on_junk():
    for spec in (None, "", "   ", ",,,", "A:0", "!!:5"):
        assert parse_spec(spec) == [(DEFAULT_VARIANT, 1)]


def test_parse_spec_drops_only_the_broken_entry():
    assert parse_spec("A:50,!!:10,B:50") == [("A", 50), ("B", 50)]
    assert parse_spec("A:50,B:xx") == [("A", 50)]


def test_single_variant_is_always_chosen():
    assert choose_variant("A") == "A"
    assert choose_variant("Z") == "Z"


def test_weights_are_respected():
    rng = random.Random(20260807)
    picks = [choose_variant("A:90,B:10", rng=rng) for _ in range(2000)]
    a_share = picks.count("A") / len(picks)
    assert 0.85 < a_share < 0.95, a_share
    assert set(picks) == {"A", "B"}


def test_normalize_variant_rejects_junk():
    assert normalize_variant("b") == "B"
    assert normalize_variant("  a1 ") == "A1"
    assert normalize_variant("!!") == DEFAULT_VARIANT
    assert normalize_variant(None) == DEFAULT_VARIANT
    assert len(normalize_variant("X" * 40)) <= 8


def test_known_variants_lists_every_bucket():
    assert known_variants("A:70,B:30") == ["A", "B"]


# --------------------------- sessiya va savollar ---------------------------


def test_session_records_its_variant(client):
    token = complete_session(client)
    with db_session(client) as db:
        assert session_by_token(db, token).variant == DEFAULT_VARIANT


def test_second_variant_can_be_seeded_alongside_the_first(client):
    """order_number endi to'plam ichida noyob — ikkinchi to'plam sig'ishi kerak."""
    with db_session(client) as db:
        added = seed_personality_questions(db, variant="B")
        assert added > 0

        a_count = len(db.scalars(select(PersonalityQuestion).where(PersonalityQuestion.variant == "A")).all())
        b_count = len(db.scalars(select(PersonalityQuestion).where(PersonalityQuestion.variant == "B")).all())

    assert a_count == b_count == added


def test_questions_are_isolated_per_variant(client):
    from app.repositories.personality_repository import PersonalityRepository

    with db_session(client) as db:
        seed_personality_questions(db, variant="B")
        repo = PersonalityRepository(db)
        a_ids = {q.id for q in repo.get_active_questions_ordered("A")}
        b_ids = {q.id for q in repo.get_active_questions_ordered("B")}

    assert a_ids and b_ids
    assert not (a_ids & b_ids)


def test_visitor_gets_questions_from_the_assigned_variant(client, monkeypatch):
    """B to'plamiga tayinlangan foydalanuvchi A savollarini ko'rmasligi kerak."""
    from app.repositories.personality_repository import PersonalityRepository

    with db_session(client) as db:
        seed_personality_questions(db, variant="B")
        # B to'plamining birinchi savolini ajratib qo'yamiz.
        repo = PersonalityRepository(db)
        b_first = repo.get_active_questions_ordered("B")[0]
        b_first.text = "B TO‘PLAMI BIRINCHI SAVOLI"
        b_question_id = b_first.id
        db.commit()

    monkeypatch.setattr(settings, "question_variants", "B")

    client.get("/personality")
    client.get("/personality/instructions")
    start = client.post("/personality/start", data={"gender": "male"}, follow_redirects=False)
    token = start.headers["location"].rstrip("/").split("/")[-1]

    page = client.get(f"/personality/test/{token}")

    assert "B TO‘PLAMI BIRINCHI SAVOLI" in page.text
    assert f'value="{b_question_id}"' in page.text
    with db_session(client) as db:
        assert session_by_token(db, token).variant == "B"


def test_variant_does_not_change_mid_test(client, monkeypatch):
    """Taqsimot o'zgarsa ham boshlangan sessiya o'z to'plamida qolishi kerak."""
    token = complete_session(client)
    monkeypatch.setattr(settings, "question_variants", "B")
    with db_session(client) as db:
        assert session_by_token(db, token).variant == DEFAULT_VARIANT


# --------------------------- hisobot ---------------------------


def test_variant_stats_reports_the_funnel(client):
    token = complete_session(client)
    with db_session(client) as db:
        session_by_token(db, token).is_premium = True
        db.commit()
        rows = AdminAnalyticsService(db).variant_stats()

    assert len(rows) == 1
    row = rows[0]
    assert row.variant == DEFAULT_VARIANT
    assert row.completed >= 1
    assert row.premium == 1


def _add_session(db, suffix: str, variant: str) -> None:
    db.add(
        PersonalityTestSession(
            token=f"t-{suffix}", payment_code=f"pc-{suffix}", share_code=f"sc-{suffix}", variant=variant
        )
    )


def test_variant_stats_separates_buckets(client):
    with db_session(client) as db:
        _add_session(db, "var-a", "A")
        _add_session(db, "var-b", "B")
        db.commit()
        rows = {row.variant: row for row in AdminAnalyticsService(db).variant_stats()}

    assert set(rows) == {"A", "B"}
    assert rows["A"].visitors == 1
    assert rows["B"].visitors == 1
    assert rows["B"].completed == 0


def test_variant_rates_handle_empty_buckets():
    empty = VariantStats(variant="B", visitors=0, completed=0, premium=0)
    assert empty.completion_rate == 0.0
    assert empty.premium_rate == 0.0

    full = VariantStats(variant="A", visitors=200, completed=50, premium=10)
    assert full.completion_rate == 25.0
    assert full.premium_rate == 20.0


def test_dashboard_hides_the_table_for_a_single_variant(client):
    client.post("/admin/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    page = client.get("/admin")
    assert "Savol to‘plamlari" not in page.text


def test_dashboard_shows_the_table_when_a_second_variant_exists(client):
    with db_session(client) as db:
        _add_session(db, "dash-a", "A")
        _add_session(db, "dash-b", "B")
        db.commit()

    client.post("/admin/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    page = client.get("/admin")

    assert "Savol to‘plamlari" in page.text

"""Referal: do'st taklif qilib bepul premium olish.

Bu funksiya tabiatan suiiste'mol qilinadi, shuning uchun testlarning yarmi aynan
"bunday qilib bo'lmasligi kerak" holatlariga tegishli.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.enums import NotificationStatus, PersonalitySessionStatus
from app.models.notification import NotificationOutbox
from app.models.personality import PersonalityTestSession
from app.personality.session_binding import make_result_access_token
from app.services import referral_service
from app.services.notification_outbox import REFERRAL_REWARD
from app.services.premium_access import has_premium_access, trial_days_left
from tests.helpers import complete_session, db_session, session_by_token


def share_code(client, token: str) -> str:
    with db_session(client) as db:
        code = session_by_token(db, token).share_code
    assert code, "sessiyada share_code yo'q"
    return code


def refer_and_complete(client, code: str, *, count: int = 1) -> list[str]:
    """`count` ta YANGI brauzerda havola bo'yicha kelib testni tugatadi."""
    tokens = []
    for _ in range(count):
        client.cookies.clear()
        assert client.get(f"/personality?ref={code}").status_code == 200
        tokens.append(complete_session(client))
    return tokens


def referrer_row(client, token: str) -> PersonalityTestSession:
    with db_session(client) as db:
        row = session_by_token(db, token)
        db.refresh(row)
        return row


# --------------------------- biriktirish ---------------------------


def test_the_result_page_shows_a_referral_link_with_the_share_code(client):
    token = complete_session(client)
    code = share_code(client, token)
    required = settings.referral_required_completions

    page = client.get(f"/personality/result/{token}")
    assert f"/personality?ref={code}" in page.text
    assert "Premiumni bepul oching" in page.text
    assert f"{required} do‘st orqali bepul ochish" in page.text


def _result_page(client, token: str):
    access = make_result_access_token(token)
    return client.get(f"/personality/result/{token}?access={access}")


def test_referral_progress_ui_shows_each_milestone_state(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)
    required = settings.referral_required_completions

    page = _result_page(client, referrer)
    assert f"0 / {required} do‘st testni tugatdi" in page.text
    assert f"Yana {required} ta qoldi" in page.text
    assert f"{required} ta do‘stingiz testni oxirigacha tugatsa" in page.text

    for done in range(1, required):
        refer_and_complete(client, code, count=1)
        page = _result_page(client, referrer)
        assert f"{done} / {required} do‘st testni tugatdi" in page.text
        assert f"Yana {required - done} ta qoldi" in page.text

    refer_and_complete(client, code, count=1)
    page = _result_page(client, referrer)
    assert "Premium natijangiz ochildi" in page.text
    assert f"{required} do‘st orqali bepul ochish" not in page.text


def test_self_referral_with_the_same_telegram_account_does_not_count(client):
    """Yangi brauzerda o'z havolangni bosish — bir xil Telegram hisob sanalmasin."""
    from sqlalchemy import select

    referrer = complete_session(client)
    code = share_code(client, referrer)
    telegram_id = 424242
    with db_session(client) as db:
        session_by_token(db, referrer).telegram_user_id = telegram_id
        db.commit()

    client.cookies.clear()
    client.get(f"/personality?ref={code}")
    with db_session(client) as db:
        referred = db.scalars(
            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)
        ).one()
        referred.telegram_user_id = telegram_id
        db.commit()

    complete_session(client)

    row = referrer_row(client, referrer)
    assert has_premium_access(row) is False
    assert row.referral_milestones_granted == 0
    with db_session(client) as db:
        assert referral_service.completed_referral_count(db, row.id) == 0


def test_the_same_referred_session_never_counts_twice(client):
    """Bitta taklif qilingan sessiya ikki marta sanalmaydi."""
    referrer = complete_session(client)
    code = share_code(client, referrer)
    tokens = refer_and_complete(client, code, count=settings.referral_required_completions)

    with db_session(client) as db:
        last = session_by_token(db, tokens[-1])
        before = referral_service.completed_referral_count(db, session_by_token(db, referrer).id)
        again = referral_service.reward_referrer_if_earned(db, last)
        after = referral_service.completed_referral_count(db, session_by_token(db, referrer).id)

    assert before == settings.referral_required_completions
    assert again is None
    assert after == before


def test_a_visitor_arriving_by_the_link_is_attributed_to_the_referrer(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)

    client.cookies.clear()
    assert client.get(f"/personality?ref={code}").status_code == 200

    with db_session(client) as db:
        referrer_id = session_by_token(db, referrer).id
        newest = db.scalars(
            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)
        ).one()
        assert newest.referred_by_session_id == referrer_id


def test_the_public_share_page_cta_carries_the_referral_code(client):
    token = complete_session(client)
    code = share_code(client, token)

    page = client.get(f"/r/{code}")
    assert page.status_code == 200
    assert f'href="/personality?ref={code}"' in page.text


def test_an_unknown_code_attributes_nobody(client):
    client.cookies.clear()
    assert client.get("/personality?ref=bunday-kod-yoq").status_code == 200

    with db_session(client) as db:
        newest = db.scalars(
            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)
        ).one()
        assert newest.referred_by_session_id is None


def test_an_unfinished_session_cannot_be_a_referrer(client):
    """Faqat testni tugatgan odamning havolasi ishlaydi."""
    from tests.helpers import start_session

    half_done = start_session(client)
    with db_session(client) as db:
        code = session_by_token(db, half_done).share_code

    client.cookies.clear()
    client.get(f"/personality?ref={code}")

    with db_session(client) as db:
        newest = db.scalars(
            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)
        ).one()
        assert newest.referred_by_session_id is None


def test_a_browser_that_already_finished_a_test_is_not_counted(client):
    """O'z havolangni o'zing bosish (va bitta brauzerda qayta topshirish) yo'li."""
    referrer = complete_session(client)
    code = share_code(client, referrer)

    # Cookie TOZALANMAYDI: shu brauzerda tugatilgan test bor. Yangi sessiya
    # ochilib, havola AYNAN unga qo'llanadi — bu suiiste'molning eng arzon yo'li.
    client.post("/personality/restart", follow_redirects=False)
    assert client.get(f"/personality?ref={code}").status_code == 200
    retake = complete_session(client)

    with db_session(client) as db:
        assert session_by_token(db, retake).referred_by_session_id is None
    assert has_premium_access(referrer_row(client, referrer)) is False


def test_an_already_started_session_cannot_be_attributed_afterwards(client):
    """Boshlangan testni keyin kimningdir hisobiga o'tkazib bo'lmaydi."""
    from tests.helpers import answer_question, start_session

    referrer = complete_session(client)
    code = share_code(client, referrer)

    client.cookies.clear()
    victim = start_session(client)
    answer_question(client, victim, 0)

    client.get(f"/personality?ref={code}")
    with db_session(client) as db:
        assert session_by_token(db, victim).referred_by_session_id is None


def test_a_visitor_who_only_looked_around_can_still_be_attributed_later(client):
    """Kecha kirib chiqqan, bugun do'stining havolasi bilan qaytgan odam."""
    referrer = complete_session(client)
    code = share_code(client, referrer)

    client.cookies.clear()
    assert client.get("/personality").status_code == 200  # oddiy tashrif
    assert client.get(f"/personality?ref={code}").status_code == 200

    with db_session(client) as db:
        referrer_id = session_by_token(db, referrer).id
        newest = db.scalars(
            select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1)
        ).one()
        assert newest.referred_by_session_id == referrer_id


# --------------------------- mukofot ---------------------------


def test_two_completed_referrals_open_premium_for_three_days(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=settings.referral_required_completions)

    row = referrer_row(client, referrer)
    assert row.is_premium is False, "bepul mukofot to'lovga aylanmasligi kerak"
    assert has_premium_access(row) is True
    assert trial_days_left(row) == settings.referral_reward_days
    assert row.referral_milestones_granted == 1


def test_an_unfinished_referral_does_not_count(client):
    from tests.helpers import start_session

    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=settings.referral_required_completions - 1)
    client.cookies.clear()
    client.get(f"/personality?ref={code}")
    start_session(client)  # boshladi, lekin tugatmadi

    row = referrer_row(client, referrer)
    assert has_premium_access(row) is False
    assert row.referral_milestones_granted == 0


def test_the_fourth_referral_does_not_grant_a_second_reward(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=settings.referral_required_completions)
    first = referrer_row(client, referrer).premium_until

    refer_and_complete(client, code, count=1)
    row = referrer_row(client, referrer)
    assert row.referral_milestones_granted == 1
    assert row.premium_until == first


def test_the_next_milestone_extends_the_existing_expiry(client):
    """Ikkinchi mukofot birinchisidan qolgan kunlarni O'CHIRMAYDI."""
    required = settings.referral_required_completions
    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=required)
    first = referrer_row(client, referrer).premium_until
    refer_and_complete(client, code, count=required)
    row = referrer_row(client, referrer)

    assert row.referral_milestones_granted == 2
    assert row.premium_until > first
    assert trial_days_left(row) == settings.referral_reward_days * 2


def test_the_total_free_period_is_capped(client, monkeypatch):
    monkeypatch.setattr(settings, "referral_max_reward_days", 4)
    required = settings.referral_required_completions
    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=required * 2)

    row = referrer_row(client, referrer)
    assert trial_days_left(row) == 4


def test_a_disabled_program_attributes_nothing_and_hides_the_block(client, monkeypatch):
    monkeypatch.setattr(settings, "referral_enabled", False)
    referrer = complete_session(client)
    code = share_code(client, referrer)

    page = client.get(f"/personality/result/{referrer}")
    assert "?ref=" not in page.text

    refer_and_complete(client, code, count=settings.referral_required_completions)
    row = referrer_row(client, referrer)
    assert has_premium_access(row) is False


# --------------------------- premium kirish huquqi ---------------------------


def _grant_trial(client, token: str, *, days: int) -> None:
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.premium_until = datetime.now(timezone.utc) + timedelta(days=days)
        db.commit()


def test_a_trial_unlocks_the_premium_sections_but_not_the_pdf(client):
    """PDF ataylab faqat to'langan premiumda: fayl muddatdan keyin ham qo'lda qoladi."""
    token = complete_session(client)
    _grant_trial(client, token, days=3)

    page = client.get(f"/personality/result/{token}")
    assert "is-locked" not in page.text
    assert f"/personality/result/{token}/pdf" not in page.text

    pdf = client.get(f"/personality/result/{token}/pdf", follow_redirects=False)
    assert pdf.status_code == 303


def test_an_expired_trial_locks_the_sections_again(client):
    token = complete_session(client)
    _grant_trial(client, token, days=-1)

    page = client.get(f"/personality/result/{token}")
    assert "is-locked" in page.text


def test_a_trial_user_can_still_buy_permanent_premium(client):
    """Sinov muddati sotib olishni to'sib qo'ymasligi kerak."""
    token = complete_session(client)
    _grant_trial(client, token, days=3)

    started = client.post(f"/personality/result/{token}/support-bot", follow_redirects=False)
    assert started.status_code == 303
    with db_session(client) as db:
        session = session_by_token(db, token)
        assert session.premium_requested is True
        assert session.payment_requests, "to'lov yozuvi yaratilishi kerak"


def test_a_trial_is_not_counted_as_a_sale_in_the_dashboard(client):
    from app.services.admin_analytics_service import AdminAnalyticsService

    token = complete_session(client)
    _grant_trial(client, token, days=3)

    with db_session(client) as db:
        variants = AdminAnalyticsService(db).variant_stats()
        growth = AdminAnalyticsService(db).growth_stats()
    assert sum(row.premium for row in variants) == 0
    assert growth.active_trials == 1


# --------------------------- bildirishnoma ---------------------------


def test_the_reward_is_announced_to_a_telegram_user(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)
    with db_session(client) as db:
        session_by_token(db, referrer).telegram_user_id = 987654
        db.commit()

    refer_and_complete(client, code, count=settings.referral_required_completions)

    with db_session(client) as db:
        rows = list(db.scalars(select(NotificationOutbox).where(NotificationOutbox.kind == REFERRAL_REWARD)))
    assert len(rows) == 1
    assert rows[0].chat_id == 987654
    assert rows[0].params["days"] == settings.referral_reward_days
    assert rows[0].status == NotificationStatus.PENDING.value


def test_no_notification_without_a_telegram_account(client):
    referrer = complete_session(client)
    code = share_code(client, referrer)

    refer_and_complete(client, code, count=settings.referral_required_completions)

    with db_session(client) as db:
        rows = list(db.scalars(select(NotificationOutbox).where(NotificationOutbox.kind == REFERRAL_REWARD)))
    assert rows == []


def test_an_expired_reward_message_is_cancelled_instead_of_lying(client):
    from app.bot import messages
    from app.bot.messages import Outcome

    token = complete_session(client)
    _grant_trial(client, token, days=-1)

    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        built = messages.referral_reward_message(db, session_id, 3)

    assert isinstance(built, Outcome)
    assert built.status == NotificationStatus.CANCELLED.value


def test_a_live_reward_message_names_the_remaining_days(client):
    from app.bot import messages
    from app.bot.messages import Message

    token = complete_session(client)
    _grant_trial(client, token, days=3)

    with db_session(client) as db:
        built = messages.referral_reward_message(db, session_by_token(db, token).id, 3)

    assert isinstance(built, Message)
    assert "3 kunga" in built.text


# --------------------------- xizmat qatlami ---------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("abc-DEF_123", "abc-DEF_123"),
        ("  kod  ", "kod"),
        ("", None),
        (None, None),
        ("kod bilan probel", None),
        ("' OR 1=1 --", None),
        ("x" * 25, None),
    ],
)
def test_code_normalisation_rejects_anything_unexpected(raw, expected):
    assert referral_service.normalize_code(raw) == expected


def test_a_second_concurrent_grant_is_refused_by_the_compare_and_swap(client):
    """Ikki do'st bir lahzada tugatsa ham mukofot ikki marta berilmaydi."""
    referrer = complete_session(client)
    code = share_code(client, referrer)
    tokens = refer_and_complete(client, code, count=settings.referral_required_completions)

    with db_session(client) as db:
        last = session_by_token(db, tokens[-1])
        assert last.status == PersonalitySessionStatus.COMPLETED
        # Xuddi shu chaqiruv ikkinchi marta bajarilsa hech narsa o'zgarmaydi.
        again = referral_service.reward_referrer_if_earned(db, last)
    assert again is None
    assert referrer_row(client, referrer).referral_milestones_granted == 1


def test_a_broken_link_shows_the_landing_page_not_an_error(client):
    """Kesilgan yoki buzilgan havola 422 bermasligi kerak."""
    for bad in ("x" * 200, "kod bilan probel", "%20", "../../etc/passwd"):
        page = client.get("/personality", params={"ref": bad})
        assert page.status_code == 200, (bad, page.status_code)


def test_an_unknown_advice_notice_does_not_break_the_result_page(client):
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}", params={"notice": "z" * 200})
    assert page.status_code == 200

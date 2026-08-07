"""Jamoa / HR rejimi: kirish nazorati, a'zolik va tarkib tahlili."""

import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.team_service import PoleBalance, composition, create_team, team_by_manage
from tests.helpers import complete_session, db_session, session_by_token

MANAGE_RE = re.compile(r"/team/manage/([A-Za-z0-9_-]+)")
INVITE_RE = re.compile(r"/team/join/([A-Za-z0-9_-]+)")


def _create_team(client, name: str = "Marketing") -> tuple[str, str]:
    """Jamoa yaratadi va (manage_code, invite_code) qaytaradi."""
    response = client.post("/team/create", data={"name": name}, follow_redirects=False)
    assert response.status_code == 303
    manage_code = MANAGE_RE.search(response.headers["location"]).group(1)
    dashboard = client.get(f"/team/manage/{manage_code}")
    invite_code = INVITE_RE.search(dashboard.text).group(1)
    return manage_code, invite_code


def _member_joins(invite_code: str, name: str, *, option_index: int = 0) -> None:
    """Har a'zo alohida brauzer: o'z sessiyasi bilan testni tugatib jamoaga qo'shiladi."""
    with TestClient(app) as member:
        complete_session(member, option_index=option_index)
        response = member.post(
            f"/team/join/{invite_code}", data={"display_name": name}, follow_redirects=False
        )
        assert response.status_code == 303, response.status_code


# --------------------------- kodlar va kirish ---------------------------


def test_create_team_issues_two_distinct_codes(client):
    manage_code, invite_code = _create_team(client)
    assert manage_code != invite_code
    assert len(manage_code) >= 10 and len(invite_code) >= 10


def test_invite_code_cannot_open_the_dashboard(client):
    """Taklif havolasini olgan xodim boshqalarning natijasini ko'rmasligi kerak."""
    _, invite_code = _create_team(client)
    assert client.get(f"/team/manage/{invite_code}").status_code == 404


def test_manage_code_cannot_be_used_as_an_invite(client):
    manage_code, _ = _create_team(client)
    assert client.get(f"/team/join/{manage_code}").status_code == 404


def test_unknown_codes_return_404(client):
    assert client.get("/team/manage/yoq-kod").status_code == 404
    assert client.get("/team/join/yoq-kod").status_code == 404


def test_empty_name_is_rejected(client):
    response = client.post("/team/create", data={"name": "   "}, follow_redirects=False)
    assert response.status_code == 400


def test_dashboard_is_noindex(client):
    manage_code, _ = _create_team(client)
    assert "noindex" in client.get(f"/team/manage/{manage_code}").text


# --------------------------- qo'shilish ---------------------------


def test_join_requires_a_completed_test(client):
    _, invite_code = _create_team(client)
    with TestClient(app) as visitor:
        response = visitor.post(
            f"/team/join/{invite_code}", data={"display_name": "Anvar"}, follow_redirects=False
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/personality"


def test_join_page_offers_the_test_when_there_is_no_result(client):
    _, invite_code = _create_team(client)
    with TestClient(app) as visitor:
        page = visitor.get(f"/team/join/{invite_code}")
    assert page.status_code == 200
    assert "/personality" in page.text


def test_member_appears_on_the_dashboard(client):
    manage_code, invite_code = _create_team(client)
    _member_joins(invite_code, "Dilnoza")

    dashboard = client.get(f"/team/manage/{manage_code}")

    assert "Dilnoza" in dashboard.text


def test_the_same_session_cannot_be_counted_twice(client):
    manage_code, invite_code = _create_team(client)
    with TestClient(app) as member:
        complete_session(member)
        member.post(f"/team/join/{invite_code}", data={"display_name": "Anvar"})
        member.post(f"/team/join/{invite_code}", data={"display_name": "Anvar qayta"})

    with db_session(client) as db:
        team = team_by_manage(db, manage_code)
        result = composition(db, team)

    assert result.size == 1
    assert result.members[0].display_name == "Anvar qayta"


def test_dashboard_never_exposes_session_tokens(client):
    """Panelda faqat ism va tip bo'lishi kerak — token natijaga to'liq kirish huquqi."""
    manage_code, invite_code = _create_team(client)
    with TestClient(app) as member:
        token = complete_session(member)
        member.post(f"/team/join/{invite_code}", data={"display_name": "Anvar"})

    dashboard = client.get(f"/team/manage/{manage_code}").text

    assert token not in dashboard
    with db_session(client) as db:
        assert session_by_token(db, token).payment_code not in dashboard


# --------------------------- tarkib tahlili ---------------------------


def test_composition_counts_types_and_members(client):
    manage_code, invite_code = _create_team(client)
    _member_joins(invite_code, "A", option_index=0)
    _member_joins(invite_code, "B", option_index=0)
    _member_joins(invite_code, "C", option_index=-1)

    with db_session(client) as db:
        result = composition(db, team_by_manage(db, manage_code))

    assert result.size == 3
    assert result.distinct_types == 2
    # Ko'p uchragan tip birinchi bo'lib turishi kerak.
    assert result.type_counts[0][1] == 2


def test_incomplete_session_is_excluded_from_the_composition(client):
    """Natija qayta hisoblanib holat o'zgarsa, a'zo tarkibdan chiqib ketishi kerak."""
    from app.models.enums import PersonalitySessionStatus

    manage_code, invite_code = _create_team(client)
    with TestClient(app) as member:
        token = complete_session(member)
        member.post(f"/team/join/{invite_code}", data={"display_name": "Anvar"})

    with db_session(client) as db:
        session_by_token(db, token).status = PersonalitySessionStatus.IN_PROGRESS
        db.commit()
        result = composition(db, team_by_manage(db, manage_code))

    assert result.size == 0


def test_balance_flags_a_skewed_team(client):
    from app.i18n import t

    manage_code, invite_code = _create_team(client)
    for name in ("A", "B", "C", "D"):
        _member_joins(invite_code, name, option_index=0)

    with db_session(client) as db:
        result = composition(db, team_by_manage(db, manage_code))

    # Hamma bir xil javob bergani uchun har o'lchov to'liq bir tomonga qiyshaygan.
    for balance in result.balances:
        assert balance.dominant_letter is not None
        assert balance.missing_letter is not None

    dashboard = client.get(f"/team/manage/{manage_code}").text
    assert t("team.insight_title", "uz") in dashboard
    # Yetishmayotgan qutb aynan nomi bilan aytilishi kerak.
    missing = result.balances[0].missing_letter.lower()
    assert t(f"dimension.{missing}", "uz") in dashboard


def test_pole_balance_percentages():
    balance = PoleBalance("E", "I", 3, 1)
    assert balance.total == 4
    assert balance.left_percent == 75
    assert balance.right_percent == 25
    assert balance.dominant_letter == "E"
    assert balance.missing_letter is None


def test_pole_balance_handles_an_empty_team():
    balance = PoleBalance("E", "I", 0, 0)
    assert balance.left_percent == 50
    assert balance.dominant_letter is None
    assert balance.missing_letter is None


def test_balanced_team_is_not_flagged():
    balance = PoleBalance("E", "I", 2, 2)
    assert balance.dominant_letter is None
    assert balance.missing_letter is None


def test_create_team_rejects_blank_names(client):
    import pytest

    with db_session(client) as db, pytest.raises(ValueError):
        create_team(db, "   ")

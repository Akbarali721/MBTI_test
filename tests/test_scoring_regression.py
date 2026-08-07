"""P0 regressiyasi: variant → qutb mappingi.

Bag shu yerda edi: variant tartibi bilan ball yoʻnalishi mos kelmagan, natijada
foydalanuvchi teskari tipni olardi. Test uchidan-uchiga (HTML forma orqali) ishlaydi,
shuning uchun shablon, marshrut yoki servis qatlamidagi har qanday siljish koʻrinadi.
"""

import pytest

from tests.helpers import complete_session, db_session, session_by_token

# Har savolning dastlabki ikki varianti chap qutb, keyingi ikkitasi oʻng qutb.
LEFT_POLE_TYPE = "ESTJ"
RIGHT_POLE_TYPE = "INFP"

OPPOSITE_LETTER = {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}


def _result_type(client, token: str) -> str:
    with db_session(client) as db:
        return session_by_token(db, token).result_type


@pytest.mark.parametrize(
    ("option_index", "expected_type"),
    [(0, LEFT_POLE_TYPE), (1, LEFT_POLE_TYPE), (2, RIGHT_POLE_TYPE), (3, RIGHT_POLE_TYPE)],
)
def test_every_option_slot_maps_to_its_pole(client, option_index, expected_type):
    token = complete_session(client, option_index=option_index)
    assert _result_type(client, token) == expected_type


def test_first_and_last_option_paths_are_exact_opposites(client):
    first_token = complete_session(client, option_index=0)
    client.cookies.clear()
    last_token = complete_session(client, option_index=-1)

    first_type = _result_type(client, first_token)
    last_type = _result_type(client, last_token)

    assert first_type == LEFT_POLE_TYPE
    assert last_type == RIGHT_POLE_TYPE
    assert last_type == "".join(OPPOSITE_LETTER[letter] for letter in first_type)


def test_dimension_scores_mirror_between_the_two_paths(client):
    first_token = complete_session(client, option_index=0)
    client.cookies.clear()
    last_token = complete_session(client, option_index=-1)

    with db_session(client) as db:
        first = session_by_token(db, first_token)
        last = session_by_token(db, last_token)
        pairs = [("e", "i"), ("s", "n"), ("t", "f"), ("j", "p")]
        for left, right in pairs:
            assert getattr(first, f"{left}_score") == getattr(last, f"{right}_score")
            assert getattr(first, f"{right}_score") == getattr(last, f"{left}_score")
            assert getattr(first, f"{left}_score") > getattr(first, f"{right}_score")


def test_result_page_shows_the_computed_type(client):
    token = complete_session(client)
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert f"<strong>{LEFT_POLE_TYPE}</strong>" in page.text

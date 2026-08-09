"""P0 regressiyasi: variant → qutb mappingi (weighted 3/1/1/3)."""

import pytest
from sqlalchemy import select

from app.models.personality import PersonalityQuestion
from app.seed.personality_placeholders import DIMENSION_POLES
from tests.helpers import complete_session, db_session, session_by_token

OPPOSITE_LETTER = {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}


def _favor_left_option_index(question):
    left, _right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == left else 3


def _favor_right_option_index(question):
    _left, right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == right else 3


def _result_type(client, token: str) -> str:
    with db_session(client) as db:
        return session_by_token(db, token).result_type


@pytest.mark.parametrize("option_index", [0, 1, 2, 3])
def test_option_slot_direction_within_question(client, option_index):
    """Har bir variant o'z qutbiga +3/+1 beradi (primary yoki opposite)."""
    with db_session(client) as db:
        question = db.scalars(select(PersonalityQuestion).limit(1)).first()
        assert question is not None
        left, right = DIMENSION_POLES[question.dimension]
        primary = question.primary_pole
        opposite = right if primary == left else left
        options = sorted(question.options, key=lambda o: o.order_number)
        opt = options[option_index]
        if option_index < 2:
            assert getattr(opt, f"{primary}_score") in (1, 3)
        else:
            assert getattr(opt, f"{opposite}_score") in (1, 3)


def test_left_favoring_path_is_opposite_of_right_favoring_path(client):
    first_token = complete_session(client, option_picker=_favor_left_option_index)
    client.cookies.clear()
    last_token = complete_session(client, option_picker=_favor_right_option_index)

    first_type = _result_type(client, first_token)
    last_type = _result_type(client, last_token)

    assert last_type == "".join(OPPOSITE_LETTER[letter] for letter in first_type)


def test_result_page_shows_the_computed_type(client):
    token = complete_session(client, option_picker=_favor_left_option_index)
    with db_session(client) as db:
        result_type = session_by_token(db, token).result_type
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert f"<strong>{result_type}</strong>" in page.text

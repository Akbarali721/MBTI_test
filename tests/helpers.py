"""Testlar uchun umumiy yordamchilar.

Sessiyani yakunlash oqimi bir necha faylda nusxalangan edi — endi u faqat shu yerda.
Oqim JSʼsiz: har savol oddiy forma POSTʼi bilan yuboriladi, natija egalik tekshiruvidan
oʻtgan cookie bilan ochiladi, toʻlov kodi esa sessiya qatoridan oʻqiladi.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.personality import PersonalityQuestion, PersonalityTestSession
from app.seed.personality_placeholders import DIMENSION_POLES

# Savollar soni seedʼdan keladi; sikl cheksiz aylanib qolmasligi uchun yuqori chegara.
MAX_QUESTIONS = 100

_OPTION_ID_RE = re.compile(r'name="option_id"\s+value="(\d+)"')


def token_from_location(location: str) -> str:
    return location.split("?", 1)[0].rstrip("/").split("/")[-1]


def extract_hidden(html: str, name: str) -> int:
    match = re.search(rf'name="{re.escape(name)}"\s+value="(\d+)"', html)
    assert match, f'"{name}" yashirin maydoni topilmadi'
    return int(match.group(1))


def option_ids(html: str) -> list[int]:
    ids = [int(value) for value in _OPTION_ID_RE.findall(html)]
    assert ids, "option_id inputlari topilmadi"
    return ids


def first_option_id(html: str) -> int:
    return option_ids(html)[0]


def last_option_id(html: str) -> int:
    return option_ids(html)[-1]


@contextmanager
def db_session(client) -> Iterator[Session]:
    """Test enginega bogʻlangan sessiya (fixture yaratgan fabrika orqali)."""
    db: Session = client.testing_session_factory()  # type: ignore[attr-defined]
    try:
        yield db
    finally:
        db.close()


def session_by_token(db: Session, token: str) -> PersonalityTestSession:
    row = db.scalar(select(PersonalityTestSession).where(PersonalityTestSession.token == token))
    assert row is not None, f"sessiya topilmadi: {token}"
    return row


def latest_session(db: Session) -> PersonalityTestSession:
    row = db.scalar(select(PersonalityTestSession).order_by(PersonalityTestSession.id.desc()).limit(1))
    assert row is not None, "hech qanday sessiya yaratilmagan"
    return row


def session_id_for_token(client, token: str) -> int:
    with db_session(client) as db:
        return session_by_token(db, token).id


def payment_code_for_token(client, token: str) -> str:
    """Natija sahifasi koʻrsatadigan test kodi (sessiya qatorida saqlanadi)."""
    with db_session(client) as db:
        code = session_by_token(db, token).payment_code
    assert code, "sessiyada payment_code yoʻq"
    return code


def favor_left_option_index(question: PersonalityQuestion) -> int:
    left, _right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == left else 3


def favor_right_option_index(question: PersonalityQuestion) -> int:
    _left, right = DIMENSION_POLES[question.dimension]
    return 0 if question.primary_pole == right else 3


def start_session(client, gender: str = "male") -> str:
    """Koʻrsatma sahifasidan oʻtib yangi test tokenini qaytaradi."""
    instructions = client.get("/personality/instructions")
    assert instructions.status_code == 200
    start = client.post("/personality/start", data={"gender": gender}, follow_redirects=False)
    assert start.status_code == 303, start.status_code
    return token_from_location(start.headers["location"])


def answer_question(
    client,
    token: str,
    question_index: int,
    *,
    option_index: int = 0,
    option_picker=None,
) -> str:
    """Bitta savolga javob beradi va serverning keyingi manzilini qaytaradi."""
    page = client.get(f"/personality/test/{token}?q={question_index}")
    assert page.status_code == 200
    if option_picker is not None:
        from tests.helpers import extract_hidden as _extract_hidden

        qid = _extract_hidden(page.text, "question_id")
        with db_session(client) as db:
            from app.models.personality import PersonalityQuestion

            question = db.get(PersonalityQuestion, qid)
            assert question is not None
            picked = option_picker(question)
        option_index = picked
    response = client.post(
        f"/personality/test/{token}/answer",
        data={
            "question_id": extract_hidden(page.text, "question_id"),
            "option_id": option_ids(page.text)[option_index],
            "question_index": str(question_index),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"]


def complete_session(
    client,
    gender: str = "male",
    *,
    option_index: int = 0,
    option_picker=None,
    open_result: bool = True,
) -> str:
    """Testni oxirigacha yakunlaydi va tokenni qaytaradi.

    option_index — har savolda tanlanadigan variant tartibi (0 chap qutb, -1 oʻng qutb).
    """
    token = start_session(client, gender)
    question_index = 0
    while True:
        location = answer_question(
            client, token, question_index, option_index=option_index, option_picker=option_picker
        )
        if location.endswith("/loading"):
            break
        question_index += 1
        assert question_index < MAX_QUESTIONS, "test yakunlanmadi"

    assert client.get(f"/personality/result/{token}/loading").status_code == 200
    if open_result:
        assert client.get(f"/personality/result/{token}").status_code == 200
    return token


def admin_login(client):
    response = client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response

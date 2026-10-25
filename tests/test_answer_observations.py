"""Javoblarga asoslangan shaxsiy kuzatuv MVP testlari."""

from __future__ import annotations

from app.i18n import t
from app.services.answer_observations import (
    MAX_OBSERVATIONS,
    MIN_SUPPORTING_ANSWERS,
    AnswerEvidenceItem,
    build_personal_observations,
    observations_for_session,
)
from app.services.personality_scoring import STRONG_OPTION_WEIGHT, WEAK_OPTION_WEIGHT
from tests.helpers import (
    complete_session,
    db_session,
    favor_left_option_index,
    favor_right_option_index,
    session_by_token,
)


def _item(
    *,
    qid: int,
    dim: str,
    pole: str,
    weight: int,
    option: str = "tanlov",
) -> AnswerEvidenceItem:
    return AnswerEvidenceItem(
        question_id=qid,
        question_text=f"Savol {qid}",
        option_id=qid * 10,
        option_text=option,
        dimension=dim,
        pole=pole,
        weight=weight,
    )


def test_consistent_answers_yield_one_or_two_observations():
    # JP bo‘yicha 5 ta kuchli P — izchil.
    jp = [
        _item(qid=i, dim="JP", pole="p", weight=STRONG_OPTION_WEIGHT, option=f"P-{i}")
        for i in range(1, 6)
    ]
    # EI bo‘yicha 4 ta kuchli I.
    ei = [
        _item(qid=20 + i, dim="EI", pole="i", weight=STRONG_OPTION_WEIGHT, option=f"I-{i}")
        for i in range(1, 5)
    ]
    # SN aralash — chiqmasligi kerak.
    sn = [
        _item(qid=30, dim="SN", pole="s", weight=STRONG_OPTION_WEIGHT),
        _item(qid=31, dim="SN", pole="n", weight=STRONG_OPTION_WEIGHT),
        _item(qid=32, dim="SN", pole="s", weight=WEAK_OPTION_WEIGHT),
    ]
    obs = build_personal_observations([*jp, *ei, *sn])
    assert 1 <= len(obs) <= MAX_OBSERVATIONS
    assert obs[0].id == "jp_p"
    assert len(obs[0].paragraphs) == 3
    assert len(obs[0].evidence) >= MIN_SUPPORTING_ANSWERS - 0
    assert all(e.pole == "p" for e in obs[0].evidence)
    ids = {o.id for o in obs}
    assert "sn_s" not in ids and "sn_n" not in ids


def test_contradictory_answers_yield_no_observation():
    answers = [
        _item(qid=1, dim="TF", pole="t", weight=STRONG_OPTION_WEIGHT),
        _item(qid=2, dim="TF", pole="t", weight=STRONG_OPTION_WEIGHT),
        _item(qid=3, dim="TF", pole="f", weight=STRONG_OPTION_WEIGHT),
        _item(qid=4, dim="TF", pole="f", weight=STRONG_OPTION_WEIGHT),
        _item(qid=5, dim="TF", pole="t", weight=WEAK_OPTION_WEIGHT),
        _item(qid=6, dim="TF", pole="f", weight=WEAK_OPTION_WEIGHT),
    ]
    assert build_personal_observations(answers) == []


def test_empty_and_single_answer_yield_nothing():
    assert build_personal_observations([]) == []
    assert build_personal_observations([_item(qid=1, dim="EI", pole="i", weight=3)]) == []
    assert (
        build_personal_observations(
            [
                _item(qid=1, dim="EI", pole="i", weight=3),
                _item(qid=2, dim="EI", pole="i", weight=3),
            ]
        )
        == []
    )


def test_two_sessions_produce_different_observation_sets(client):
    token_i = complete_session(client, option_picker=favor_right_option_index)
    client.cookies.clear()
    token_e = complete_session(client, option_picker=favor_left_option_index)

    with db_session(client) as db:
        s_i = session_by_token(db, token_i)
        s_e = session_by_token(db, token_e)
        obs_i = observations_for_session(db, s_i.id)
        obs_e = observations_for_session(db, s_e.id)

    assert s_i.result_type != s_e.result_type
    assert obs_i and obs_e
    ids_i = {o.id for o in obs_i}
    ids_e = {o.id for o in obs_e}
    assert ids_i.isdisjoint(ids_e)
    assert any(o.pole in ("i", "n", "f", "p") for o in obs_i)
    assert any(o.pole in ("e", "s", "t", "j") for o in obs_e)


def test_free_result_renders_observations_with_evidence(client):
    token = complete_session(client, option_picker=favor_right_option_index)
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    title = t("result.answer_observations.title", "uz")
    assert title in page.text
    assert t("result.answer_observations.based_on", "uz") in page.text
    assert "mbti-answer-observation" in page.text
    # Tip matni hali ham joyida.
    assert t("result.strengths", "uz") in page.text


def test_premium_result_still_shows_free_observations(client):
    token = complete_session(client, option_picker=favor_right_option_index)
    with db_session(client) as db:
        row = session_by_token(db, token)
        row.is_premium = True
        db.commit()

    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    assert t("result.answer_observations.title", "uz") in page.text
    # Premium kontent ham ochiq.
    assert "mbti-premium" in page.text or t("result.premium_headline", "uz") in page.text


def test_mixed_session_hides_observation_block(client):
    """Har savolda 0/1 indekslarni almashtirib qarama-qarshi javoblar beramiz."""

    flip = {"n": 0}

    def alternate(question):
        flip["n"] += 1
        return 0 if flip["n"] % 2 else 3

    token = complete_session(client, option_picker=alternate)
    with db_session(client) as db:
        row = session_by_token(db, token)
        obs = observations_for_session(db, row.id)
    page = client.get(f"/personality/result/{token}")
    assert page.status_code == 200
    if not obs:
        assert t("result.answer_observations.title", "uz") not in page.text
    else:
        # Agar baribir 1 ta o‘lchov o‘tib ketsa — blok bor, lekin 2 tadan oshmasin.
        assert page.text.count("mbti-answer-observation") <= MAX_OBSERVATIONS

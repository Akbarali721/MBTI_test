"""Javoblarga asoslangan 1–2 ta shaxsiy kuzatuv (MVP).

Mavjud scoring o‘zgarmaydi: bu modul faqat allaqachon saqlangan javoblarni
o‘qiydi va izchil dalil bo‘lsa hayotiy kuzatuv matnini yig‘adi.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PersonalityDimension
from app.models.personality import PersonalityAnswer, PersonalityOption, PersonalityQuestion
from app.services.personality_scoring import STRONG_OPTION_WEIGHT

# Kamida shuncha izchil javob bo‘lishi kerak — bitta javobdan hukm chiqarilmaydi.
MIN_SUPPORTING_ANSWERS = 3
# Qarama-qarshi kuchli javoblar shundan oshsa — o‘lchov noaniq, kuzatuv yo‘q.
MAX_OPPOSING_STRONG = 1
# Dominant qutbning sof og‘irligi (3/1 ball) shu chegaradan past bo‘lsa — yetarli emas.
MIN_NET_WEIGHT = 7
# Sahifada ko‘rsatiladigan eng ko‘p kuzatuv.
MAX_OBSERVATIONS = 2
# Har kuzatuv ostida ko‘rsatiladigan tanlovlar soni.
MAX_EVIDENCE_ITEMS = 3

SCORE_KEYS = ("e", "i", "s", "n", "t", "f", "j", "p")

DIMENSION_POLES: dict[PersonalityDimension, tuple[str, str]] = {
    PersonalityDimension.EI: ("e", "i"),
    PersonalityDimension.SN: ("s", "n"),
    PersonalityDimension.TF: ("t", "f"),
    PersonalityDimension.JP: ("j", "p"),
}

# Hayotiy, yumshoq kuzatuvlar — tip matnidan mustaqil, faqat o‘lchov+qutb bo‘yicha.
_OBSERVATION_COPY: dict[tuple[str, str], tuple[str, str, str]] = {
    ("ei", "i"): (
        "Siz bo‘sh vaqt yoki yangi guruhda ko‘pincha avval o‘zingizga joy qoldirasiz.",
        "Bu yolg‘izlik istagi emas — fikrni tartibga solib, keyin odamlarga ochilish usuli.",
        "Shuning uchun tinch muhitda ish va suhbat sizga odatda osonroq ketadi.",
    ),
    ("ei", "e"): (
        "Siz yangi odamlar yoki guruh bilan bo‘lganda tezroq jonlanasiz.",
        "Fikrni ovoz chiqarib aytsangiz, u sizda tezroq shakllanadi.",
        "Uzoq yolg‘iz qolganda esa energiya sezilarli pasayishi mumkin.",
    ),
    ("sn", "s"): (
        "Siz yangi ishni tushunishda aniq misol, tartib va «hozir qanday ishlaydi»ni qidirasiz.",
        "Umumiy g‘oya yaxshi, lekin qo‘lga ilinadigan detal bo‘lmasa ishonchingiz sekinroq o‘sadi.",
        "Shuning uchun amaliy qadamlar sizga tezroq yo‘l ochadi.",
    ),
    ("sn", "n"): (
        "Siz avval umumiy manzarani va «nega»sini ko‘rishni xohlaysiz.",
        "Faqat qoidalar ro‘yxati berilsa, ichingizda hali yo‘nalish yetishmayotgandek tuyulishi mumkin.",
        "Ma’no va bog‘lanishlar ochilganda esa tezroq chuqurlashasiz.",
    ),
    ("tf", "t"): (
        "Qaror qabul qilganda siz uchun mezon, natija va mantiqiy izchillik muhim.",
        "His-tuyg‘uni e’tiborsiz qoldirmaysiz, lekin tanlovni asosan «nima ishlaydi» bilan o‘lchaysiz.",
        "Shuning uchun noaniq bahs sizni tezroq charchatishi mumkin.",
    ),
    ("tf", "f"): (
        "Tanlovda siz odamlarga ta’sir va o‘z qadriyatingizni hisobga olasiz.",
        "Faqat «eng samarali» yo‘l ba’zan siz uchun to‘liq javob bo‘lmaydi.",
        "Yaqinlarning holati e’tiborga olinganda qaror sizga to‘g‘riroq tuyuladi.",
    ),
    ("jp", "j"): (
        "Siz ishni oldindan bosqichlarga bo‘lib olganingizda xotirjamroq harakat qilasiz.",
        "Reja o‘zgarganda moslashasiz, lekin avval yangi tartibni belgilab olishni xohlaysiz.",
        "Aniq muddat va tayyorlik mezoni sizga kuch beradi.",
    ),
    ("jp", "p"): (
        "Sizga qattiq jadvaldan ko‘ra o‘z ritmingizda ishlash qulayroq.",
        "Asosiy yo‘nalishni bilib, keyingi qadamlarni jarayonda tanlash sizga tabiiyroq.",
        "Hamma narsa oldindan mahkam belgilansa, energiya pasayishi mumkin.",
    ),
}


@dataclass(frozen=True)
class AnswerEvidenceItem:
    question_id: int
    question_text: str
    option_id: int
    option_text: str
    dimension: str
    pole: str
    weight: int


@dataclass(frozen=True)
class PersonalObservation:
    id: str
    dimension: str
    pole: str
    paragraphs: tuple[str, ...]
    evidence: tuple[AnswerEvidenceItem, ...]
    strength: int


def _active_pole_and_weight(option: PersonalityOption) -> tuple[str, int] | None:
    for key in SCORE_KEYS:
        value = int(getattr(option, f"{key}_score") or 0)
        if value > 0:
            return key, value
    return None


def load_answer_evidence(db: Session, session_id: int) -> list[AnswerEvidenceItem]:
    """Sessiyaning tanlangan javoblarini kuzatuv uchun yassi ro‘yxatga aylantiradi."""
    stmt = (
        select(PersonalityAnswer, PersonalityQuestion, PersonalityOption)
        .join(PersonalityQuestion, PersonalityAnswer.question_id == PersonalityQuestion.id)
        .join(PersonalityOption, PersonalityAnswer.option_id == PersonalityOption.id)
        .where(PersonalityAnswer.session_id == session_id)
        .order_by(PersonalityAnswer.id.asc())
    )
    rows = db.execute(stmt).all()
    items: list[AnswerEvidenceItem] = []
    for _answer, question, option in rows:
        pole_weight = _active_pole_and_weight(option)
        if pole_weight is None:
            continue
        pole, weight = pole_weight
        items.append(
            AnswerEvidenceItem(
                question_id=question.id,
                question_text=(question.text or "").strip(),
                option_id=option.id,
                option_text=(option.text or "").strip(),
                dimension=str(question.dimension.value),
                pole=pole,
                weight=weight,
            )
        )
    return items


def _dimension_candidates(
    answers: Iterable[AnswerEvidenceItem],
) -> list[PersonalObservation]:
    by_dim: dict[str, list[AnswerEvidenceItem]] = {}
    for item in answers:
        by_dim.setdefault(item.dimension, []).append(item)

    candidates: list[PersonalObservation] = []
    for dim_key, dim_answers in by_dim.items():
        try:
            dimension = PersonalityDimension(dim_key)
        except ValueError:
            continue
        left, right = DIMENSION_POLES[dimension]
        buckets: dict[str, list[AnswerEvidenceItem]] = {left: [], right: []}
        for item in dim_answers:
            if item.pole in buckets:
                buckets[item.pole].append(item)

        left_weight = sum(i.weight for i in buckets[left])
        right_weight = sum(i.weight for i in buckets[right])
        if left_weight == right_weight:
            continue
        dominant = left if left_weight > right_weight else right
        other = right if dominant == left else left
        supporting = buckets[dominant]
        opposing = buckets[other]
        opposing_strong = sum(1 for i in opposing if i.weight >= STRONG_OPTION_WEIGHT)
        net = sum(i.weight for i in supporting) - sum(i.weight for i in opposing)

        if len(supporting) < MIN_SUPPORTING_ANSWERS:
            continue
        if opposing_strong > MAX_OPPOSING_STRONG:
            continue
        if net < MIN_NET_WEIGHT:
            continue

        dim_norm = dim_key.lower()
        copy = _OBSERVATION_COPY.get((dim_norm, dominant))
        if not copy:
            continue

        # Eng kuchli dalillarni oldinga: avval +3, keyin +1.
        ranked = sorted(supporting, key=lambda i: (-i.weight, i.question_id))
        evidence = tuple(ranked[:MAX_EVIDENCE_ITEMS])
        candidates.append(
            PersonalObservation(
                id=f"{dim_norm}_{dominant}",
                dimension=dim_norm,
                pole=dominant,
                paragraphs=copy,
                evidence=evidence,
                strength=net,
            )
        )

    candidates.sort(key=lambda o: (-o.strength, o.id))
    return candidates


def build_personal_observations(
    answers: Iterable[AnswerEvidenceItem],
    *,
    limit: int = MAX_OBSERVATIONS,
) -> list[PersonalObservation]:
    """Izchil dalildan 0..limit ta kuzatuv. Scoringga tegmaydi."""
    if limit <= 0:
        return []
    items = list(answers)
    if not items:
        return []
    return _dimension_candidates(items)[:limit]


def observations_for_session(db: Session, session_id: int) -> list[PersonalObservation]:
    return build_personal_observations(load_answer_evidence(db, session_id))


def observations_for_template(observations: list[PersonalObservation]) -> list[dict]:
    """Jinja uchun sodda dictlar."""
    payload: list[dict] = []
    for obs in observations:
        payload.append(
            {
                "id": obs.id,
                "dimension": obs.dimension,
                "pole": obs.pole,
                "paragraphs": list(obs.paragraphs),
                "evidence": [
                    {
                        "question_text": e.question_text,
                        "option_text": e.option_text,
                    }
                    for e in obs.evidence
                ],
            }
        )
    return payload


# Testlar uchun eksport (og‘irliklar o‘zgarmaganini tekshirish osonlashadi).
__all__ = [
    "AnswerEvidenceItem",
    "PersonalObservation",
    "MIN_SUPPORTING_ANSWERS",
    "MAX_OPPOSING_STRONG",
    "MIN_NET_WEIGHT",
    "MAX_OBSERVATIONS",
    "STRONG_OPTION_WEIGHT",
    "build_personal_observations",
    "load_answer_evidence",
    "observations_for_session",
    "observations_for_template",
]

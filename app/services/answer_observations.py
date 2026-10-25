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

@dataclass(frozen=True)
class ObservationCopy:
    title: str
    paragraphs: tuple[str, ...]
    tip: str


# Hayotiy matn — tip katalogidan mustaqil. EI = muloqot/energiya, JP = reja/moslashuv.
# Maslahatlar free natijadagi «chegara aytish / ziddiyat / qadriyat qadami»ni takrorlamaydi.
_OBSERVATION_COPY: dict[tuple[str, str], ObservationCopy] = {
    ("ei", "i"): ObservationCopy(
        title="Avval o‘zingizga joy qoldirasiz",
        paragraphs=(
            "Yangi davra yoki bo‘sh vaqtda siz odatda avval jimroq turasiz.",
            "Bu yolg‘izlik emas: avval o‘ylaysiz, keyin odamlarga ochilasiz.",
            "Tinch joyda gaplashish va ishlash sizga osonroq ketadi.",
        ),
        tip="Keyingi uchrashuvda 5 daqiqa jim o‘tirib oling, keyin bitta odamga gap oching.",
    ),
    ("ei", "e"): ObservationCopy(
        title="Odamlar orasida tezroq jonlanasiz",
        paragraphs=(
            "Siz guruhda yoki yangi tanishlar bilan bo‘lganda odatda tezroq kuch topasiz.",
            "Fikrni ovoz chiqarib aytganingizda u sizda tezroq shakllanadi.",
            "Uzoq yolg‘iz qolsangiz, charchoq tezroq sezilishi mumkin.",
        ),
        tip="Bugun bitta fikrni avval do‘stingizga aytib ko‘ring, keyin yolg‘iz qayta o‘ylang.",
    ),
    ("sn", "s"): ObservationCopy(
        title="Avval aniq misol kerak bo‘ladi",
        paragraphs=(
            "Yangi ishni tushunishda siz «hozir qanday ishlaydi?» ni qidirasiz.",
            "Umumiy g‘oya yaxshi, lekin qo‘lga ilinadigan detal bo‘lmasa ishonch sekinroq o‘sadi.",
        ),
        tip="Yangi vazifada avval bitta real misol yoki namuna so‘rang.",
    ),
    ("sn", "n"): ObservationCopy(
        title="Avval katta rasmni ko‘rasiz",
        paragraphs=(
            "Siz avval ishning ma’nosini va «nega»sini tushunishni xohlaysiz.",
            "Faqat qoidalar ro‘yxati berilsa, yo‘nalish yetishmayotgandek tuyulishi mumkin.",
        ),
        tip="Qoidalarni o‘qishdan oldin «bu nima uchun kerak?» ni bir jumlada yozing.",
    ),
    ("tf", "t"): ObservationCopy(
        title="Qarorda natija ustun turadi",
        paragraphs=(
            "Tanlovda siz uchun mezon va «nima ishlaydi» muhim.",
            "His-tuyg‘uni e’tiborsiz qoldirmaysiz, lekin yakuniy o‘lchov odatda natija bo‘ladi.",
        ),
        tip="Qaror oldidan ikkita qator yozing: nima ishlaydi va nima ishlamaydi.",
    ),
    ("tf", "f"): ObservationCopy(
        title="Qarorda odamlar ham hisobga olinadi",
        paragraphs=(
            "Tanlovda siz yaqinlarning holati va o‘z qadriyatingizni ham o‘ylaysiz.",
            "Faqat «eng tez natija» ba’zan siz uchun to‘liq javob bo‘lmaydi.",
        ),
        tip="Qaror oldidan «bu kimga qanday ta’sir qiladi?» ni bir jumlada yozing.",
    ),
    ("jp", "j"): ObservationCopy(
        title="Avval tartib, keyin harakat",
        paragraphs=(
            "Siz ishni oldindan qadamlarga bo‘lib olganingizda xotirjamroq ishlaysiz.",
            "Reja o‘zgarsa, avval yangi tartibni belgilab, keyin davom etasiz.",
            "Aniq muddat sizga yo‘l-yo‘riq beradi.",
        ),
        tip="Reja o‘zgarsa, yangi tartibni uch qatorda yozib oling, keyin ishni davom ettiring.",
    ),
    ("jp", "p"): ObservationCopy(
        title="Rejani ish davomida tuzasiz",
        paragraphs=(
            "Sizga qattiq jadvaldan ko‘ra yo‘lni borib turib tanlash qulayroq.",
            "Yo‘nalishni bilib, keyingi qadamni jarayonda belgilash sizga tabiiy.",
            "Hamma narsa oldindan mahkam qilinsa, ishning o‘zi og‘irlashishi mumkin.",
        ),
        tip="Bugun ishning faqat birinchi qismini belgilang. Qolganini kechqurun qaroring.",
    ),
}

# Muloqot (EI) va rejalashtirish (JP) birga chiqsa — tartib aniq farqlansin.
_PREFERRED_DIMENSION_ORDER = ("ei", "jp", "sn", "tf")
QUESTION_PREVIEW_MAX = 90


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
    title: str
    paragraphs: tuple[str, ...]
    tip: str
    evidence: tuple[AnswerEvidenceItem, ...]
    strength: int


def question_preview(text: str, *, max_len: int = QUESTION_PREVIEW_MAX) -> str:
    """Savolni qisqartirish: to‘liq gap yoki birinchi jumla. Uch nuqta qo‘yilmaydi."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    for sep in (". ", "? ", "! "):
        if sep in cleaned:
            first = cleaned.split(sep, 1)[0].strip()
            if len(first) >= 18:
                end = sep[0]
                if not first.endswith((".", "?", "!")):
                    first = f"{first}{end}"
                return first
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned.rfind(" ", 0, max_len)
    if cut < 24:
        return cleaned
    return cleaned[:cut].rstrip(".,;:")


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
                title=copy.title,
                paragraphs=copy.paragraphs,
                tip=copy.tip,
                evidence=evidence,
                strength=net,
            )
        )

    return candidates


def _select_observations(
    candidates: list[PersonalObservation],
    limit: int,
) -> list[PersonalObservation]:
    """Kuchli dalilni saqlab, mumkin bo‘lsa avval EI (muloqot), keyin JP (reja)."""
    if limit <= 0 or not candidates:
        return []
    by_dim = {item.dimension: item for item in candidates}
    chosen: list[PersonalObservation] = []
    for dim in _PREFERRED_DIMENSION_ORDER:
        if len(chosen) >= limit:
            break
        item = by_dim.get(dim)
        if item is not None:
            chosen.append(item)
    if len(chosen) < limit:
        rest = [item for item in candidates if item not in chosen]
        rest.sort(key=lambda o: (-o.strength, o.id))
        chosen.extend(rest[: limit - len(chosen)])
    return chosen[:limit]


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
    return _select_observations(_dimension_candidates(items), limit)


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
                "title": obs.title,
                "paragraphs": list(obs.paragraphs),
                "tip": obs.tip,
                "evidence": [
                    {
                        "question_text": question_preview(e.question_text),
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
    "ObservationCopy",
    "PersonalObservation",
    "question_preview",
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

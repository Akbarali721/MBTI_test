"""Scoring and type resolution for E/I, S/N, T/F, J/P dimensions.

Tie-break (when dimension totals are equal after weighted scoring):
1. Compare sum of +3 ("strong") contributions per pole from answered items.
2. If still tied, compare sum of +1 ("weak") contributions per pole.
3. If still tied, deterministic hash on `tie_salt` and dimension (see `_resolve_letter`).
"""

from dataclasses import dataclass

from app.personality.constants import DIMENSION_LOW_CONFIDENCE_MAX_GAP

STRONG_OPTION_WEIGHT = 3
WEAK_OPTION_WEIGHT = 1


@dataclass(frozen=True)
class DimensionPairPercent:
    left_label: str
    left_percent: int
    right_label: str
    right_percent: int
    low_confidence: bool = False


@dataclass(frozen=True)
class PersonalityScores:
    e: int
    i: int
    s: int
    n: int
    t: int
    f: int
    j: int
    p: int


@dataclass(frozen=True)
class PersonalityResult:
    result_type: str
    scores: PersonalityScores
    ei: DimensionPairPercent
    sn: DimensionPairPercent
    tf: DimensionPairPercent
    jp: DimensionPairPercent


def _pair_percent(
    left_score: int,
    right_score: int,
    left_label: str,
    right_label: str,
    *,
    low_confidence: bool,
) -> DimensionPairPercent:
    total = left_score + right_score
    if total == 0:
        return DimensionPairPercent(left_label, 50, right_label, 50, low_confidence=low_confidence)
    left_percent = round(left_score / total * 100)
    right_percent = 100 - left_percent
    return DimensionPairPercent(
        left_label, left_percent, right_label, right_percent, low_confidence=low_confidence
    )


def _is_low_confidence(left_score: int, right_score: int) -> bool:
    return abs(left_score - right_score) <= DIMENSION_LOW_CONFIDENCE_MAX_GAP


def _resolve_letter(
    left_score: int,
    right_score: int,
    left_letter: str,
    right_letter: str,
    *,
    strong_left: int,
    strong_right: int,
    weak_left: int,
    weak_right: int,
    tie_salt: str,
) -> tuple[str, bool]:
    low_confidence = _is_low_confidence(left_score, right_score)
    if left_score > right_score:
        return left_letter, low_confidence
    if right_score > left_score:
        return right_letter, low_confidence

    low_confidence = True
    if strong_left > strong_right:
        return left_letter, low_confidence
    if strong_right > strong_left:
        return right_letter, low_confidence
    if weak_left > weak_right:
        return left_letter, low_confidence
    if weak_right > weak_left:
        return right_letter, low_confidence
    # Session-deterministic coin flip — avoids always picking the first pole letter.
    if hash((tie_salt, left_letter, right_letter)) % 2 == 0:
        return left_letter, low_confidence
    return right_letter, low_confidence


def calculate_personality_result(
    e: int,
    i: int,
    s: int,
    n: int,
    t: int,
    f: int,
    j: int,
    p: int,
    *,
    strong_e: int = 0,
    strong_i: int = 0,
    strong_s: int = 0,
    strong_n: int = 0,
    strong_t: int = 0,
    strong_f: int = 0,
    strong_j: int = 0,
    strong_p: int = 0,
    weak_e: int = 0,
    weak_i: int = 0,
    weak_s: int = 0,
    weak_n: int = 0,
    weak_t: int = 0,
    weak_f: int = 0,
    weak_j: int = 0,
    weak_p: int = 0,
    tie_salt: str = "",
) -> PersonalityResult:
    scores = PersonalityScores(e=e, i=i, s=s, n=n, t=t, f=f, j=j, p=p)

    e_letter, ei_low = _resolve_letter(
        e,
        i,
        "E",
        "I",
        strong_left=strong_e,
        strong_right=strong_i,
        weak_left=weak_e,
        weak_right=weak_i,
        tie_salt=f"{tie_salt}:ei",
    )
    s_letter, sn_low = _resolve_letter(
        s,
        n,
        "S",
        "N",
        strong_left=strong_s,
        strong_right=strong_n,
        weak_left=weak_s,
        weak_right=weak_n,
        tie_salt=f"{tie_salt}:sn",
    )
    t_letter, tf_low = _resolve_letter(
        t,
        f,
        "T",
        "F",
        strong_left=strong_t,
        strong_right=strong_f,
        weak_left=weak_t,
        weak_right=weak_f,
        tie_salt=f"{tie_salt}:tf",
    )
    j_letter, jp_low = _resolve_letter(
        j,
        p,
        "J",
        "P",
        strong_left=strong_j,
        strong_right=strong_p,
        weak_left=weak_j,
        weak_right=weak_p,
        tie_salt=f"{tie_salt}:jp",
    )

    result_type = e_letter + s_letter + t_letter + j_letter
    return PersonalityResult(
        result_type=result_type,
        scores=scores,
        ei=_pair_percent(i, e, "Introvert (I)", "Ekstravert (E)", low_confidence=ei_low),
        sn=_pair_percent(s, n, "Sensor (S)", "Intuitiv (N)", low_confidence=sn_low),
        tf=_pair_percent(t, f, "Mantiqiy (T)", "Hisliy (F)", low_confidence=tf_low),
        jp=_pair_percent(j, p, "Rejalovchi (J)", "Improvisatsiya (P)", low_confidence=jp_low),
    )

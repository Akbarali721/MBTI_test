"""Scoring and type resolution for E/I, S/N, T/F, J/P dimensions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionPairPercent:
    left_label: str
    left_percent: int
    right_label: str
    right_percent: int


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


def _pair_percent(left_score: int, right_score: int, left_label: str, right_label: str) -> DimensionPairPercent:
    total = left_score + right_score
    if total == 0:
        return DimensionPairPercent(left_label, 50, right_label, 50)
    left_percent = round(left_score / total * 100)
    right_percent = 100 - left_percent
    return DimensionPairPercent(left_label, left_percent, right_label, right_percent)


def _winning_letter(left_score: int, right_score: int, left_letter: str, right_letter: str) -> str:
    if left_score >= right_score:
        return left_letter
    return right_letter


def calculate_personality_result(
    e: int,
    i: int,
    s: int,
    n: int,
    t: int,
    f: int,
    j: int,
    p: int,
) -> PersonalityResult:
    scores = PersonalityScores(e=e, i=i, s=s, n=n, t=t, f=f, j=j, p=p)
    result_type = (
        _winning_letter(e, i, "E", "I")
        + _winning_letter(s, n, "S", "N")
        + _winning_letter(t, f, "T", "F")
        + _winning_letter(j, p, "J", "P")
    )
    return PersonalityResult(
        result_type=result_type,
        scores=scores,
        ei=_pair_percent(i, e, "Introvert (I)", "Ekstravert (E)"),
        sn=_pair_percent(s, n, "Sensor (S)", "Intuitiv (N)"),
        tf=_pair_percent(t, f, "Mantiqiy (T)", "Hisliy (F)"),
        jp=_pair_percent(j, p, "Rejalovchi (J)", "Improvisatsiya (P)"),
    )

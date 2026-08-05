from app.services.personality_scoring import calculate_personality_result

ALL_TYPES = {
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
}


def test_zero_scores_default_to_fifty_fifty():
    result = calculate_personality_result(0, 0, 0, 0, 0, 0, 0, 0)
    assert result.result_type == "ESTJ"
    assert result.ei.left_percent == 50 and result.ei.right_percent == 50


def test_all_sixteen_types_are_reachable():
    seen = set()
    patterns = [
        (8, 0, 8, 0, 8, 0, 8, 0),
        (0, 8, 0, 8, 0, 8, 0, 8),
        (8, 4, 8, 4, 8, 4, 8, 4),
        (4, 8, 4, 8, 4, 8, 4, 8),
        (6, 2, 2, 6, 6, 2, 2, 6),
        (2, 6, 6, 2, 2, 6, 6, 2),
    ]
    for pattern in patterns:
        e, i, s, n, t, f, j, p = pattern
        seen.add(calculate_personality_result(e, i, s, n, t, f, j, p).result_type)
    for combo in range(16):
        bits = [(combo >> shift) & 1 for shift in range(4)]
        scores = []
        for bit in bits:
            scores.extend((8, 0) if bit == 0 else (0, 8))
        seen.add(calculate_personality_result(*scores).result_type)
    assert seen == ALL_TYPES


def test_percentage_sums_to_one_hundred():
    result = calculate_personality_result(3, 7, 1, 9, 5, 5, 2, 8)
    for pair in (result.ei, result.sn, result.tf, result.jp):
        assert pair.left_percent + pair.right_percent == 100

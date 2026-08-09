"""Weighted scoring and tie handling."""

from app.services.personality_scoring import calculate_personality_result


def test_exact_total_tie_uses_strong_votes_not_first_pole():
    """Equal E/I totals: stronger side wins; no default E."""
    result = calculate_personality_result(
        9,
        9,
        10,
        5,
        8,
        8,
        7,
        7,
        strong_e=6,
        strong_i=9,
        tie_salt="test-token",
    )
    assert result.result_type[0] == "I"
    assert result.ei.low_confidence is True


def test_exact_tie_without_strong_bias_uses_hash_not_always_e():
    """Two salts can flip E/I; neither path uses left_score > right_score shortcut."""
    salts = [f"tie-salt-{n}" for n in range(32)]
    letters = {calculate_personality_result(6, 6, 12, 6, 12, 6, 12, 6, tie_salt=s).result_type[0] for s in salts}
    assert "E" in letters and "I" in letters


def test_clear_winner_not_low_confidence():
    result = calculate_personality_result(18, 6, 12, 6, 12, 6, 12, 6, tie_salt="x")
    assert result.result_type[0] == "E"
    assert result.ei.low_confidence is False

"""Premium natija 6 bo'limli taqdimot."""

from types import SimpleNamespace

from app.seed.personality_results_uz import get_result_copy
from app.services.premium_presentation import compose_premium_blocks


def test_compose_premium_blocks_returns_six_sections():
    copy = get_result_copy("INFP")
    content = SimpleNamespace(**copy)
    blocks = compose_premium_blocks(
        content,
        copy["strengths"],
        copy["challenges"],
        language="uz",
    )
    assert len(blocks) == 6
    assert blocks[0].title_key == "result.premium.brief"
    assert blocks[0].body
    assert blocks[1].title_key == "result.premium.strengths"
    assert len(blocks[1].bullets) == 3
    assert blocks[2].title_key == "result.premium.drains"
    assert len(blocks[2].bullets) >= 2
    assert blocks[3].sub_bullets
    assert blocks[5].bullets

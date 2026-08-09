"""Production bank shape: 48 active, 12×4, 6+6 poles — seed must upgrade stale DBs."""

from sqlalchemy import func, select

from app.models.personality import PersonalityQuestion
from app.seed.personality_placeholders import (
    PERSONALITY_QUESTIONS_BANK,
    question_bank_is_valid,
    seed_personality_questions,
)
from tests.helpers import db_session


def test_seed_upgrades_stale_twenty_four_question_bank(client):
    with db_session(client) as db:
        for row in db.scalars(select(PersonalityQuestion)).all():
            db.delete(row)
        db.commit()

        # Legacy shape: 24 active rows (left pole only), missing reversed twins.
        base = [row for idx, row in enumerate(PERSONALITY_QUESTIONS_BANK) if idx % 2 == 0][:24]
        for order, (text, dimension, _option_texts, primary_pole) in enumerate(base, start=1):
            db.add(
                PersonalityQuestion(
                    text=text,
                    dimension=dimension,
                    order_number=order,
                    variant="A",
                    is_active=True,
                    primary_pole=primary_pole,
                )
            )
        db.commit()
        assert not question_bank_is_valid(db, "A")

        added = seed_personality_questions(db, force=False, variant="A")
        assert added == 48
        assert question_bank_is_valid(db, "A")

        active = int(
            db.scalar(
                select(func.count())
                .select_from(PersonalityQuestion)
                .where(
                    PersonalityQuestion.variant == "A",
                    PersonalityQuestion.is_active.is_(True),
                )
            )
            or 0
        )
        assert active == 48

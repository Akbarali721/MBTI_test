import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import AppearanceTheme, PersonalitySessionStatus
from app.models.personality import (
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityResultContent,
    PersonalityTestSession,
)
from app.services.personality_scoring import calculate_personality_result


class PersonalityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(
        self,
        *,
        user_id: int | None = None,
        telegram_user_id: str | None = None,
        source: str | None = None,
        status: PersonalitySessionStatus = PersonalitySessionStatus.VISITED,
    ) -> PersonalityTestSession:
        now = datetime.now(timezone.utc)
        total = self.count_active_questions()
        session = PersonalityTestSession(
            token=uuid.uuid4().hex,
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            status=status,
            current_question_index=0,
            total_questions=total,
            answered_questions=0,
            source=source,
            last_activity_at=now,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def touch_session_activity(self, session: PersonalityTestSession) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        self.db.commit()

    def set_source_if_empty(self, session: PersonalityTestSession, source: str) -> None:
        if session.source or not source:
            return
        session.source = source
        self.db.commit()

    def count_answers(self, session_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalityAnswer)
            .where(PersonalityAnswer.session_id == session_id)
        )
        return int(self.db.scalar(stmt) or 0)

    def _apply_answer_analytics(self, session: PersonalityTestSession) -> None:
        now = datetime.now(timezone.utc)
        count = self.count_answers(session.id)
        session.answered_questions = count
        session.last_activity_at = now
        if count == 0:
            self.db.commit()
            return
        if session.status == PersonalitySessionStatus.VISITED:
            session.status = PersonalitySessionStatus.STARTED
            session.started_at = session.started_at or now
        elif session.status == PersonalitySessionStatus.STARTED and count >= 2:
            session.status = PersonalitySessionStatus.IN_PROGRESS
        self.db.commit()

    def get_session_by_token(self, token: str) -> PersonalityTestSession | None:
        stmt = select(PersonalityTestSession).where(PersonalityTestSession.token == token)
        return self.db.scalar(stmt)

    def get_session_by_id(self, session_id: int) -> PersonalityTestSession | None:
        return self.db.get(PersonalityTestSession, session_id)

    def list_sessions(self, limit: int = 200) -> list[PersonalityTestSession]:
        stmt = (
            select(PersonalityTestSession)
            .order_by(PersonalityTestSession.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_active_questions(self) -> int:
        stmt = select(PersonalityQuestion).where(PersonalityQuestion.is_active.is_(True))
        return len(list(self.db.scalars(stmt).all()))

    def get_active_questions_ordered(self) -> list[PersonalityQuestion]:
        stmt = (
            select(PersonalityQuestion)
            .where(PersonalityQuestion.is_active.is_(True))
            .options(joinedload(PersonalityQuestion.options))
            .order_by(PersonalityQuestion.order_number)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_question_by_order(self, order_number: int) -> PersonalityQuestion | None:
        stmt = (
            select(PersonalityQuestion)
            .where(PersonalityQuestion.is_active.is_(True))
            .where(PersonalityQuestion.order_number == order_number)
            .options(joinedload(PersonalityQuestion.options))
        )
        return self.db.scalar(stmt)

    def get_answer_map(self, session_id: int) -> dict[int, int]:
        stmt = select(PersonalityAnswer).where(PersonalityAnswer.session_id == session_id)
        answers = self.db.scalars(stmt).all()
        return {a.question_id: a.option_id for a in answers}

    def get_option(self, option_id: int) -> PersonalityOption | None:
        return self.db.get(PersonalityOption, option_id)

    def upsert_answer(self, session_id: int, question_id: int, option_id: int) -> PersonalityAnswer:
        stmt = select(PersonalityAnswer).where(
            PersonalityAnswer.session_id == session_id,
            PersonalityAnswer.question_id == question_id,
        )
        existing = self.db.scalar(stmt)
        if existing:
            existing.option_id = option_id
            answer = existing
        else:
            answer = PersonalityAnswer(session_id=session_id, question_id=question_id, option_id=option_id)
            self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        session = self.get_session_by_id(session_id)
        if session:
            self._apply_answer_analytics(session)
        return answer

    def recalculate_and_complete_session(self, session: PersonalityTestSession) -> PersonalityTestSession:
        stmt = select(PersonalityAnswer).where(PersonalityAnswer.session_id == session.id)
        answers = list(self.db.scalars(stmt).all())
        totals = {"e": 0, "i": 0, "s": 0, "n": 0, "t": 0, "f": 0, "j": 0, "p": 0}
        for answer in answers:
            option = self.get_option(answer.option_id)
            if not option:
                continue
            totals["e"] += option.e_score
            totals["i"] += option.i_score
            totals["s"] += option.s_score
            totals["n"] += option.n_score
            totals["t"] += option.t_score
            totals["f"] += option.f_score
            totals["j"] += option.j_score
            totals["p"] += option.p_score

        result = calculate_personality_result(**totals)
        session.e_score = totals["e"]
        session.i_score = totals["i"]
        session.s_score = totals["s"]
        session.n_score = totals["n"]
        session.t_score = totals["t"]
        session.f_score = totals["f"]
        session.j_score = totals["j"]
        session.p_score = totals["p"]
        session.result_type = result.result_type
        session.status = PersonalitySessionStatus.COMPLETED
        now = datetime.now(timezone.utc)
        session.completed_at = now
        session.last_activity_at = now
        session.answered_questions = session.total_questions or len(answers)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session_progress(self, session: PersonalityTestSession, index: int) -> None:
        session.current_question_index = index
        session.last_activity_at = datetime.now(timezone.utc)
        self.db.commit()

    def get_result_content(self, personality_type: str) -> PersonalityResultContent | None:
        stmt = select(PersonalityResultContent).where(
            PersonalityResultContent.personality_type == personality_type,
            PersonalityResultContent.is_active.is_(True),
        )
        return self.db.scalar(stmt)

    def set_premium(
        self,
        session_id: int,
        *,
        is_premium: bool = True,
        set_approved_at: bool = True,
    ) -> PersonalityTestSession | None:
        session = self.get_session_by_id(session_id)
        if not session:
            return None
        session.is_premium = is_premium
        if is_premium and set_approved_at:
            session.premium_approved_at = session.premium_approved_at or datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session)
        return session

    def request_premium(self, session: PersonalityTestSession) -> PersonalityTestSession:
        session.premium_requested = True
        self.db.commit()
        self.db.refresh(session)
        return session

    def set_appearance_theme(
        self, session: PersonalityTestSession, theme: AppearanceTheme
    ) -> PersonalityTestSession:
        session.appearance_theme = theme
        self.db.commit()
        self.db.refresh(session)
        return session

    @staticmethod
    def parse_json_list(raw: str) -> list[str]:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data]
        except json.JSONDecodeError:
            pass
        return [line.strip() for line in raw.splitlines() if line.strip()]

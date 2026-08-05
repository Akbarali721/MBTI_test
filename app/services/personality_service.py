from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import AppearanceTheme, PersonalitySessionStatus
from app.models.personality import PersonalityQuestion, PersonalityTestSession
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_scoring import calculate_personality_result


class PersonalityService:
    def __init__(self, db: Session) -> None:
        self.repo = PersonalityRepository(db)

    def start_session(
        self,
        *,
        user_id: int | None = None,
        telegram_user_id: str | None = None,
        source: str | None = None,
    ) -> PersonalityTestSession:
        return self.repo.create_session(
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            source=source,
        )

    def get_session_or_404(self, token: str) -> PersonalityTestSession:
        session = self.repo.get_session_by_token(token)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    def total_questions(self) -> int:
        return self.repo.count_active_questions()

    def get_test_view(self, token: str, question_index: int | None = None) -> dict:
        session = self.get_session_or_404(token)
        questions = self.repo.get_active_questions_ordered()
        total = len(questions)
        if total == 0:
            return {"redirect": "questions_error", "session": session}

        if session.status == PersonalitySessionStatus.COMPLETED:
            return {"redirect": "result", "session": session, "total": total}

        if question_index is None:
            question_index = session.current_question_index
        question_index = max(0, min(question_index, total - 1))

        question = questions[question_index]
        answer_map = self.repo.get_answer_map(session.id)
        selected_option_id = answer_map.get(question.id)

        return {
            "session": session,
            "question": question,
            "question_index": question_index,
            "total": total,
            "selected_option_id": selected_option_id,
            "progress_display": question_index + 1,
        }

    def submit_answer(
        self,
        token: str,
        *,
        question_id: int,
        option_id: int,
        question_index: int,
    ) -> dict:
        session = self.get_session_or_404(token)
        if session.status == PersonalitySessionStatus.COMPLETED:
            return {"redirect": "result", "session": session}

        questions = self.repo.get_active_questions_ordered()
        total = len(questions)
        question = self._question_by_id(questions, question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question")

        option = self.repo.get_option(option_id)
        if not option or option.question_id != question_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid option")

        self.repo.upsert_answer(session.id, question_id, option_id)

        next_index = question_index + 1
        if next_index >= total:
            self.repo.recalculate_and_complete_session(session)
            return {"redirect": "loading", "session": session}

        self.repo.update_session_progress(session, next_index)
        return {"redirect": "question", "session": session, "next_index": next_index}

    def get_result_view(self, token: str) -> dict:
        session = self.get_session_or_404(token)
        if session.status != PersonalitySessionStatus.COMPLETED or not session.result_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test not completed yet")

        content = self.repo.get_result_content(session.result_type)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result content missing for {session.result_type}",
            )

        result = calculate_personality_result(
            session.e_score,
            session.i_score,
            session.s_score,
            session.n_score,
            session.t_score,
            session.f_score,
            session.j_score,
            session.p_score,
        )

        return {
            "session": session,
            "content": content,
            "result": result,
            "strengths": self.repo.parse_json_list(content.free_strengths),
            "challenges": self.repo.parse_json_list(content.free_challenges),
        }

    def request_premium_access(self, token: str) -> PersonalityTestSession:
        session = self.get_session_or_404(token)
        if session.status != PersonalitySessionStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete the test first")
        if session.is_premium:
            return session
        return self.repo.request_premium(session)

    def grant_premium(self, session_id: int) -> PersonalityTestSession:
        session = self.repo.set_premium(session_id, is_premium=True)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    def set_appearance(self, token: str, theme: AppearanceTheme) -> PersonalityTestSession:
        session = self.get_session_or_404(token)
        return self.repo.set_appearance_theme(session, theme)

    @staticmethod
    def _question_by_id(questions: list[PersonalityQuestion], question_id: int) -> PersonalityQuestion | None:
        for q in questions:
            if q.id == question_id:
                return q
        return None

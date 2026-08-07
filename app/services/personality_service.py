import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import AppearanceTheme, PersonalitySessionStatus
from app.models.personality import (
    DEFAULT_CONTENT_LANGUAGE,
    DEFAULT_VARIANT,
    PersonalityQuestion,
    PersonalityTestSession,
)
from app.repositories.personality_repository import PersonalityRepository
from app.services import referral_service
from app.services.notification_outbox import REFERRAL_REWARD, dedup_key, enqueue
from app.services.personality_scoring import calculate_personality_result
from app.services.premium_payment_service import enqueue_premium_granted

logger = logging.getLogger(__name__)


class PersonalityService:
    def __init__(self, db: Session) -> None:
        self.repo = PersonalityRepository(db)

    def start_session(
        self,
        *,
        user_id: int | None = None,
        telegram_user_id: int | None = None,
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

    def total_questions(self, variant: str = DEFAULT_VARIANT) -> int:
        return self.repo.count_active_questions(variant)

    def get_test_view(self, token: str, question_index: int | None = None) -> dict:
        session = self.get_session_or_404(token)
        # Savollar sessiya boshlanganda tanlangan to'plamdan olinadi.
        questions = self.repo.get_active_questions_ordered(session.variant)
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

        questions = self.repo.get_active_questions_ordered(session.variant)
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
            # Referal mukofoti AYNAN shu yerda: `submit_answer` — veb va bot uchun
            # yagona tugatish nuqtasi, ya'ni mukofot ikkala kanalda ham bir xil
            # va tugatish bilan BIR tranzaksiyada beriladi.
            self._reward_referrer(session)
            return {"redirect": "loading", "session": session}

        self.repo.update_session_progress(session, next_index)
        return {"redirect": "question", "session": session, "next_index": next_index}

    def _reward_referrer(self, session: PersonalityTestSession) -> None:
        """Taklif qilgan odamga mukofot yetgan bo'lsa, uni beradi va xabar qo'yadi.

        Referal — qo'shimcha imkoniyat, testning o'zi emas: hisoblashdagi kod
        xatosi tugatilgan testni yo'q qilmasligi kerak, shuning uchun istisno
        yutiladi. Bu FAQAT tiklanadigan xatolarga yordam beradi — baza uzilgan
        bo'lsa tashqi tranzaksiya baribir yiqiladi, va bu to'g'ri: mukofot
        tugatish bilan bitta tranzaksiyada bo'lishi kerak.
        """
        try:
            reward = referral_service.reward_referrer_if_earned(self.repo.db, session)
        except Exception:
            logger.exception("Referal mukofotini hisoblab bo‘lmadi: sessiya #%s", session.id)
            return
        if reward is None or not reward.chat_id:
            return
        enqueue(
            self.repo.db,
            kind=REFERRAL_REWARD,
            chat_id=reward.chat_id,
            params={"session_id": reward.referrer_id, "days": reward.days},
            # Kalitda bosqich raqami: keyingi mukofot alohida xabar bo'lishi kerak.
            key=dedup_key(REFERRAL_REWARD, reward.chat_id, reward.referrer_id, str(reward.milestones)),
        )

    def get_result_view(self, token: str, language: str = DEFAULT_CONTENT_LANGUAGE) -> dict:
        session = self.get_session_or_404(token)
        if session.status != PersonalitySessionStatus.COMPLETED or not session.result_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test not completed yet")

        # So'ralgan til topilmasa repository "uz" ga qaytadi.
        content = self.repo.get_result_content(session.result_type, language)
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
        """Admin qo'lda premium ochadi (masalan to'lov boshqa kanal orqali kelgan).

        Tugallanmagan sessiyaga premium berib bo'lmaydi: aks holda natijasi yo'q
        sessiya "pullik" bo'lib qolardi va saqlash siyosati uchun ham chalkash
        holat yaratardi.
        """
        existing = self.repo.get_session_by_id(session_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if existing.status != PersonalitySessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Testni tugatmagan sessiyaga premium berib bo‘lmaydi",
            )
        already_premium = existing.is_premium

        session = self.repo.set_premium(session_id, is_premium=True)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        now = datetime.now(timezone.utc)
        session.premium_requested = True
        session.premium_requested_at = session.premium_requested_at or now
        self.repo.db.flush()

        if not already_premium:
            # Qo'lda ochilgan premium ham mijozga xabar qilinadi — avval bu yo'l
            # butunlay jim edi va mijoz premium ochilganini bilmasdi.
            enqueue_premium_granted(self.repo.db, session=session, chat_id=session.telegram_user_id)
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

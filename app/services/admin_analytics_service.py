from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityAnswer, PersonalityQuestion, PersonalityTestSession


@dataclass(frozen=True)
class AdminDashboardStats:
    total_visitors: int
    started_tests: int
    completed_tests: int
    incomplete_tests: int
    today_visitors: int
    completion_rate: float


class AdminAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def dashboard_stats(self) -> AdminDashboardStats:
        total = self._scalar_count(select(func.count()).select_from(PersonalityTestSession))
        completed = self._scalar_count(
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED)
        )
        started = self._scalar_count(
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(PersonalityTestSession.started_at.is_not(None))
        )
        incomplete = max(0, started - completed)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_visitors = self._scalar_count(
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(PersonalityTestSession.created_at >= today_start)
        )
        rate = (completed / started * 100.0) if started > 0 else 0.0
        return AdminDashboardStats(
            total_visitors=total,
            started_tests=started,
            completed_tests=completed,
            incomplete_tests=incomplete,
            today_visitors=today_visitors,
            completion_rate=round(rate, 1),
        )

    def list_sessions(
        self,
        *,
        status_filter: str | None = None,
        today_only: bool = False,
        payment_code: str | None = None,
        limit: int = 500,
    ) -> list[PersonalityTestSession]:
        if payment_code and payment_code.strip():
            from app.personality.payment_code import find_sessions_by_payment_code

            return find_sessions_by_payment_code(self.db, payment_code, limit=limit)
        stmt = select(PersonalityTestSession).order_by(
            PersonalityTestSession.last_activity_at.desc().nullslast(),
            PersonalityTestSession.created_at.desc(),
        )
        if status_filter and status_filter != "all":
            if status_filter == "today":
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                stmt = stmt.where(PersonalityTestSession.created_at >= today_start)
            else:
                try:
                    status = PersonalitySessionStatus(status_filter)
                    stmt = stmt.where(PersonalityTestSession.status == status)
                except ValueError:
                    pass
        elif today_only:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = stmt.where(PersonalityTestSession.created_at >= today_start)
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_session_detail(self, session_id: int) -> dict | None:
        from app.repositories.personality_repository import PersonalityRepository

        repo = PersonalityRepository(self.db)
        session = repo.get_session_by_id(session_id)
        if not session:
            return None
        stmt = (
            select(PersonalityAnswer, PersonalityQuestion)
            .join(PersonalityQuestion, PersonalityAnswer.question_id == PersonalityQuestion.id)
            .where(PersonalityAnswer.session_id == session_id)
            .order_by(PersonalityQuestion.order_number)
        )
        rows = self.db.execute(stmt).all()
        answers = []
        for answer, question in rows:
            opt = repo.get_option(answer.option_id)
            answers.append(
                {
                    "order": question.order_number,
                    "question_text": question.text,
                    "option_text": opt.text if opt else "—",
                }
            )
        return {"session": session, "answers": answers}

    def _scalar_count(self, stmt) -> int:
        return int(self.db.scalar(stmt) or 0)

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Generic, TypeVar

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import (
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityTestSession,
)

T = TypeVar("T")

# O'zbekistonda yozgi vaqt yo'q, shuning uchun qat'iy UTC+5 yetarli va tzdata talab qilmaydi.
TASHKENT_TZ = timezone(timedelta(hours=5))

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500


def tashkent_day_start(now: datetime | None = None) -> datetime:
    """Asia/Tashkent bo'yicha bugungi kun boshini UTC lahzasi sifatida qaytaradi.

    Bazadagi vaqtlar UTC'da saqlanadi, "bugun" esa admin uchun mahalliy kun bo'lishi kerak.
    """
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local_midnight = moment.astimezone(TASHKENT_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(timezone.utc)


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @property
    def pages(self) -> int:
        if self.page_size <= 0:
            return 1
        return max(1, -(-self.total // self.page_size))

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_page(self) -> int:
        return max(1, self.page - 1)

    @property
    def next_page(self) -> int:
        return min(self.pages, self.page + 1)

    @property
    def first_index(self) -> int:
        """Joriy sahifadagi birinchi qatorning umumiy ro'yxatdagi tartib raqami (1 dan)."""
        if not self.items:
            return 0
        return (self.page - 1) * self.page_size + 1

    @property
    def last_index(self) -> int:
        if not self.items:
            return 0
        return self.first_index + len(self.items) - 1


def normalize_page(page: int | None) -> int:
    return max(1, page or 1)


def normalize_page_size(page_size: int | None) -> int:
    if not page_size or page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


@dataclass(frozen=True)
class AdminDashboardStats:
    total_visitors: int
    started_tests: int
    completed_tests: int
    incomplete_tests: int
    today_visitors: int
    completion_rate: float


@dataclass(frozen=True)
class VariantStats:
    """Bitta savol to'plami bo'yicha voronka: ko'rgan -> tugatgan -> to'lagan."""

    variant: str
    visitors: int
    completed: int
    premium: int

    @property
    def completion_rate(self) -> float:
        return round(self.completed / self.visitors * 100, 1) if self.visitors else 0.0

    @property
    def premium_rate(self) -> float:
        """Konversiya tugatganlarga nisbatan — A/B da asosiy ko'rsatkich shu."""
        return round(self.premium / self.completed * 100, 1) if self.completed else 0.0


class AdminAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def variant_stats(self) -> list[VariantStats]:
        """Har to'plam uchun voronka — bitta guruhlangan so'rov bilan."""
        completed = PersonalitySessionStatus.COMPLETED
        stmt = (
            select(
                PersonalityTestSession.variant,
                func.count(),
                func.sum(case((PersonalityTestSession.status == completed, 1), else_=0)),
                func.sum(case((PersonalityTestSession.is_premium.is_(True), 1), else_=0)),
            )
            .group_by(PersonalityTestSession.variant)
            .order_by(PersonalityTestSession.variant)
        )
        return [
            VariantStats(
                variant=row[0],
                visitors=int(row[1] or 0),
                completed=int(row[2] or 0),
                premium=int(row[3] or 0),
            )
            for row in self.db.execute(stmt).all()
        ]

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
        today_visitors = self._scalar_count(
            select(func.count()).select_from(PersonalityTestSession).where(self._today_clause())
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
        return self.list_sessions_page(
            status_filter=status_filter,
            today_only=today_only,
            payment_code=payment_code,
            page=1,
            page_size=limit,
        ).items

    def list_sessions_page(
        self,
        *,
        status_filter: str | None = None,
        today_only: bool = False,
        payment_code: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Page[PersonalityTestSession]:
        page = normalize_page(page)
        page_size = normalize_page_size(page_size)

        if payment_code and payment_code.strip():
            from app.personality.payment_code import find_sessions_by_payment_code

            # Kod bo'yicha qidiruv bir nechta qatordan iborat bo'ladi: sahifalash shart emas.
            found = find_sessions_by_payment_code(self.db, payment_code, limit=page_size)
            return Page(items=found, total=len(found), page=1, page_size=page_size)

        clauses = self._filter_clauses(status_filter=status_filter, today_only=today_only)
        count_stmt = select(func.count()).select_from(PersonalityTestSession)
        stmt = select(PersonalityTestSession).order_by(
            PersonalityTestSession.last_activity_at.desc().nullslast(),
            PersonalityTestSession.created_at.desc(),
        )
        for clause in clauses:
            count_stmt = count_stmt.where(clause)
            stmt = stmt.where(clause)

        total = self._scalar_count(count_stmt)
        offset = (page - 1) * page_size
        items = list(self.db.scalars(stmt.offset(offset).limit(page_size)).all())
        return Page(items=items, total=total, page=page, page_size=page_size)

    def get_session_detail(self, session_id: int) -> dict | None:
        from app.repositories.personality_repository import PersonalityRepository

        repo = PersonalityRepository(self.db)
        session = repo.get_session_by_id(session_id)
        if not session:
            return None
        # Variant matni ham shu so'rovda keladi: har javob uchun alohida SELECT yo'q.
        stmt = (
            select(PersonalityQuestion.order_number, PersonalityQuestion.text, PersonalityOption.text)
            .select_from(PersonalityAnswer)
            .join(PersonalityQuestion, PersonalityAnswer.question_id == PersonalityQuestion.id)
            .outerjoin(PersonalityOption, PersonalityAnswer.option_id == PersonalityOption.id)
            .where(PersonalityAnswer.session_id == session_id)
            .order_by(PersonalityQuestion.order_number)
        )
        answers = [
            {"order": order, "question_text": question_text, "option_text": option_text or "—"}
            for order, question_text, option_text in self.db.execute(stmt).all()
        ]
        return {"session": session, "answers": answers}

    def _filter_clauses(
        self,
        *,
        status_filter: str | None,
        today_only: bool,
    ) -> list[ColumnElement[bool]]:
        if status_filter and status_filter != "all":
            if status_filter == "today":
                return [self._today_clause()]
            try:
                status = PersonalitySessionStatus(status_filter)
            except ValueError:
                return []
            return [PersonalityTestSession.status == status]
        if today_only:
            return [self._today_clause()]
        return []

    @staticmethod
    def _today_clause() -> ColumnElement[bool]:
        return PersonalityTestSession.created_at >= tashkent_day_start()

    def _scalar_count(self, stmt) -> int:
        return int(self.db.scalar(stmt) or 0)

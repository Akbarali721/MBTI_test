from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Generic, TypeVar

from sqlalchemy import ColumnElement, Subquery, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.analytics import SessionDailyStats
from app.models.enums import PersonalitySessionStatus
from app.models.payment_request import PAYMENT_STATUS_APPROVED, PaymentRequest
from app.models.personality import (
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityTestSession,
)
from app.timeutils import TASHKENT_TZ, as_utc, tashkent_day_start

__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "STAGE_KEYS",
    "TASHKENT_TZ",
    "AdminAnalyticsService",
    "AdminDashboardStats",
    "FunnelDay",
    "FunnelReport",
    "FunnelStage",
    "Page",
    "VariantStats",
    "normalize_page",
    "normalize_page_size",
    "payment_rollup",
    "session_stage_depth",
    "tashkent_day_start",
]

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# Voronka bosqichlari — chuqurlik tartibida. Har sessiya faqat BITTA chuqurlikka
# tegishli, bosqich sonlari esa suffiks yig'indi sifatida chiqariladi. Shu tufayli
# "keyingi bosqich oldingisidan katta" degan bema'nilik tuzilishan mumkin emas.
STAGE_KEYS: tuple[str, ...] = (
    "visited",
    "started",
    "completed",
    "payment_started",
    "receipt_sent",
    "approved",
)
DAILY_DAYS = 14


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
class FunnelStage:
    key: str
    count: int
    of_first: float
    of_previous: float


@dataclass(frozen=True)
class FunnelDay:
    # `day` — Toshkent kun boshining UTC lahzasi.
    day: datetime
    counts: tuple[int, ...]

    @property
    def label(self) -> str:
        """Sanani MAHALLIY kun sifatida ko'rsatadi.

        UTC lahzasini to'g'ridan-to'g'ri formatlash bir kun oldingi sanani berardi
        (Toshkent yarim tuni = UTC 19:00).
        """
        return self.day.astimezone(TASHKENT_TZ).strftime("%Y-%m-%d")

    @property
    def visited(self) -> int:
        return self.counts[0]

    @property
    def completed(self) -> int:
        return self.counts[2]

    @property
    def approved(self) -> int:
        return self.counts[5]


@dataclass(frozen=True)
class FunnelReport:
    stages: list[FunnelStage]
    days: list[FunnelDay]
    range_days: int | None
    variant: str | None
    premium_without_payment: int
    requested_without_payment: int

    @property
    def total(self) -> int:
        return self.stages[0].count if self.stages else 0


def payment_rollup() -> Subquery:
    """Bitta sessiyaga BITTA qator.

    To'g'ridan-to'g'ri JOIN qilib bo'lmaydi: rad etilgan chekdan keyin qayta yuborilsa
    bitta sessiyada bir nechta to'lov qatori bo'ladi va sessiya ikki marta sanalardi.
    """
    return (
        select(
            PaymentRequest.session_id.label("session_id"),
            func.max(case((PaymentRequest.receipt_sent_at.is_not(None), 1), else_=0)).label("has_receipt"),
            func.max(case((PaymentRequest.status == PAYMENT_STATUS_APPROVED, 1), else_=0)).label(
                "has_approved"
            ),
        )
        .group_by(PaymentRequest.session_id)
        .subquery()
    )


def session_stage_depth(payments: Subquery) -> ColumnElement[int]:
    """Sessiya yetgan eng chuqur bosqich (0..5)."""
    model = PersonalityTestSession
    return case(
        (or_(payments.c.has_approved == 1, model.is_premium.is_(True)), 5),
        (payments.c.has_receipt == 1, 4),
        (payments.c.session_id.is_not(None), 3),
        (model.status == PersonalitySessionStatus.COMPLETED, 2),
        # 003 migratsiyasi started_at ni backfill'siz qo'shgan: eski qatorlarda u NULL.
        (
            or_(
                model.started_at.is_not(None),
                model.status != PersonalitySessionStatus.VISITED,
            ),
            1,
        ),
        else_=0,
    )


def _day_bucket_expr(day_starts: list[datetime]) -> ColumnElement[int]:
    """Toshkent kunlari bo'yicha guruhlash — SQL sana funksiyalarisiz.

    `date()` / `date_trunc()` dialektga bog'liq va UTC kuni bo'yicha bo'lakka bo'ladi,
    ya'ni 00:00-05:00 oralig'idagi hodisa oldingi kunga tushib, dashboard'dagi
    "bugun" soni bilan ziddiyat chiqarardi.
    """
    model = PersonalityTestSession
    branches = []
    for index, start in enumerate(day_starts):
        end = start + timedelta(days=1)
        branches.append(((model.created_at >= start) & (model.created_at < end), index))
    return case(*branches, else_=-1)


def _suffix_sums(per_depth: list[int]) -> list[int]:
    """Chuqurlik bo'yicha sonlardan bosqich sonlarini chiqaradi (orqadan yig'indi)."""
    running = 0
    result = [0] * len(per_depth)
    for index in range(len(per_depth) - 1, -1, -1):
        running += per_depth[index]
        result[index] = running
    return result


def _ratio(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def _as_stages(counts: list[int]) -> list[FunnelStage]:
    first = counts[0] if counts else 0
    stages: list[FunnelStage] = []
    for index, key in enumerate(STAGE_KEYS):
        previous = counts[index - 1] if index else first
        stages.append(
            FunnelStage(
                key=key,
                count=counts[index],
                of_first=_ratio(counts[index], first),
                of_previous=_ratio(counts[index], previous) if index else (100.0 if first else 0.0),
            )
        )
    return stages


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
        """Har to'plam uchun voronka — bitta guruhlangan so'rov bilan.

        Tozalangan (o'chirilgan) sessiyalar `session_daily_stats` dan qo'shiladi,
        aks holda saqlash siyosati ishlagach har to'plamning tugatish foizi 100% ga
        yaqinlashib, A/B qarori buzilardi.
        """
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
        totals: dict[str, list[int]] = {}
        for row in self.db.execute(stmt).all():
            totals[row[0]] = [int(row[1] or 0), int(row[2] or 0), int(row[3] or 0)]

        for variant, archived in self._archived_by_variant().items():
            bucket = totals.setdefault(variant, [0, 0, 0])
            bucket[0] += archived[0]
            bucket[1] += archived[2]
            bucket[2] += archived[5]

        return [
            VariantStats(variant=variant, visitors=values[0], completed=values[1], premium=values[2])
            for variant, values in sorted(totals.items())
        ]

    def _archived_by_variant(self) -> dict[str, tuple[int, ...]]:
        """Kunlik agregatdagi (o'chirilgan sessiyalar) sonlari, to'plam kesimida."""
        stmt = select(
            SessionDailyStats.variant,
            func.sum(SessionDailyStats.visited),
            func.sum(SessionDailyStats.started),
            func.sum(SessionDailyStats.completed),
            func.sum(SessionDailyStats.payment_started),
            func.sum(SessionDailyStats.receipt_sent),
            func.sum(SessionDailyStats.approved),
        ).group_by(SessionDailyStats.variant)
        return {row[0]: tuple(int(value or 0) for value in row[1:]) for row in self.db.execute(stmt).all()}

    def funnel(self, *, days: int | None = 30, variant: str | None = None) -> FunnelReport:
        """Kogorta voronkasi: sessiyalar BIRINCHI tashrif kuni bo'yicha guruhlanadi.

        Har bosqich o'z vaqt belgisi bo'yicha filtrlanmaydi. Aks holda 40 kun oldin
        boshlangan va kecha tasdiqlangan to'lov 7 kunlik oynada "tasdiqlangan: 1,
        tashrif: 0" ko'rinishida chiqib, foizlar nolga bo'linishga olib kelardi.
        """
        day_starts = self._recent_day_starts(days)
        payments = payment_rollup()
        bucket = _day_bucket_expr(day_starts)
        depth = session_stage_depth(payments)

        stmt = (
            select(bucket.label("bucket"), depth.label("depth"), func.count())
            .select_from(PersonalityTestSession)
            .outerjoin(payments, payments.c.session_id == PersonalityTestSession.id)
            .group_by(bucket, depth)
        )
        window_start = self._window_start(days)
        if window_start is not None:
            stmt = stmt.where(PersonalityTestSession.created_at >= window_start)
        if variant:
            stmt = stmt.where(PersonalityTestSession.variant == variant)

        totals = [0] * len(STAGE_KEYS)
        per_day = [[0] * len(STAGE_KEYS) for _ in day_starts]
        for bucket_index, stage_depth, count in self.db.execute(stmt).all():
            value = int(count or 0)
            index = int(stage_depth or 0)
            totals[index] += value
            position = int(bucket_index if bucket_index is not None else -1)
            if 0 <= position < len(per_day):
                per_day[position][index] += value

        stages = _suffix_sums(totals)
        daily = [
            FunnelDay(day=start, counts=tuple(_suffix_sums(row)))
            for start, row in zip(day_starts, per_day, strict=True)
        ]
        stages, daily = self._merge_archived(stages, daily, window_start=window_start, variant=variant)

        premium_no_payment, requested_no_payment = self._payment_anomalies(window_start, variant)
        return FunnelReport(
            stages=_as_stages(stages),
            days=daily,
            range_days=days,
            variant=variant,
            premium_without_payment=premium_no_payment,
            requested_without_payment=requested_no_payment,
        )

    def _merge_archived(
        self,
        stages: list[int],
        daily: list[FunnelDay],
        *,
        window_start: datetime | None,
        variant: str | None,
    ) -> tuple[list[int], list[FunnelDay]]:
        """Agregatdagi (endi tirik bo'lmagan) sessiyalarni qo'shadi."""
        stmt = select(
            SessionDailyStats.day,
            SessionDailyStats.visited,
            SessionDailyStats.started,
            SessionDailyStats.completed,
            SessionDailyStats.payment_started,
            SessionDailyStats.receipt_sent,
            SessionDailyStats.approved,
        )
        if window_start is not None:
            stmt = stmt.where(SessionDailyStats.day >= window_start)
        if variant:
            stmt = stmt.where(SessionDailyStats.variant == variant)

        by_day = {day.day: index for index, day in enumerate(daily)}
        merged_daily = [list(day.counts) for day in daily]
        for row in self.db.execute(stmt).all():
            values = [int(value or 0) for value in row[1:]]
            for index, value in enumerate(values):
                stages[index] += value
            day_key = as_utc(row[0])
            position = by_day.get(day_key) if day_key else None
            if position is not None:
                for index, value in enumerate(values):
                    merged_daily[position][index] += value

        rebuilt = [
            FunnelDay(day=day.day, counts=tuple(counts))
            for day, counts in zip(daily, merged_daily, strict=True)
        ]
        return stages, rebuilt

    def _payment_anomalies(self, window_start: datetime | None, variant: str | None) -> tuple[int, int]:
        """Voronka yolg'on gapirmasligi uchun alohida ko'rsatiladigan holatlar."""
        payments = payment_rollup()
        base = (
            select(func.count())
            .select_from(PersonalityTestSession)
            .outerjoin(payments, payments.c.session_id == PersonalityTestSession.id)
            .where(payments.c.session_id.is_(None))
        )
        if window_start is not None:
            base = base.where(PersonalityTestSession.created_at >= window_start)
        if variant:
            base = base.where(PersonalityTestSession.variant == variant)
        granted = self._scalar_count(base.where(PersonalityTestSession.is_premium.is_(True)))
        requested = self._scalar_count(
            base.where(
                PersonalityTestSession.is_premium.is_(False),
                PersonalityTestSession.premium_requested.is_(True),
            )
        )
        return granted, requested

    @staticmethod
    def _window_start(days: int | None) -> datetime | None:
        if not days or days <= 0:
            return None
        # Chegara Toshkent yarim tunidan boshlanadi — kunlik jadval yig'indisi
        # umumiy songa teng bo'lishi uchun.
        return tashkent_day_start() - timedelta(days=days - 1)

    @staticmethod
    def _recent_day_starts(days: int | None) -> list[datetime]:
        """Kunlik jadval oynadan CHIQIB ketmasligi kerak.

        Aks holda 7 kunlik filtrda ham 14 kunlik jadval chiziladi va oyna tashqarisidagi
        kunlar nol ko'rinardi — ya'ni haqiqatan tashrif bo'lgan kun "nol" deb o'qilardi.
        """
        span = DAILY_DAYS if not days else min(DAILY_DAYS, days)
        today = tashkent_day_start()
        return [today - timedelta(days=offset) for offset in range(span - 1, -1, -1)]

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
        # Tozalangan sessiyalar agregatdan qo'shiladi: aks holda o'chirish faqat
        # maxrajni kamaytirib, tugatish foizini sun'iy ko'tarib yuborardi.
        archived = self._archived_totals()
        total += archived[0]
        started += archived[1]
        completed += archived[2]
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

    def _archived_totals(self) -> tuple[int, ...]:
        row = self.db.execute(
            select(
                func.sum(SessionDailyStats.visited),
                func.sum(SessionDailyStats.started),
                func.sum(SessionDailyStats.completed),
                func.sum(SessionDailyStats.payment_started),
                func.sum(SessionDailyStats.receipt_sent),
                func.sum(SessionDailyStats.approved),
            )
        ).one()
        return tuple(int(value or 0) for value in row)

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

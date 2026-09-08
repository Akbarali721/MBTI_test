"""Admin: Telegram foydalanuvchilari ro'yxati va voronka."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramReferral, TelegramUser
from app.personality.test_progress import progress_percent, progress_reached, progress_status_label, progress_total
from app.services.admin_analytics_service import Page, normalize_page, normalize_page_size
from app.services.premium_access import has_premium_access
from app.services.telegram_user_service import list_referrals_for_referrer, primary_session_for_telegram_user
from app.timeutils import utcnow

FILTER_ALL = "all"
FILTER_TEST_STARTED = "test_started"
FILTER_TEST_COMPLETED = "test_completed"
FILTER_NOT_COMPLETED = "not_completed"
FILTER_PREMIUM = "premium"
FILTER_REFERRED = "referred"

FILTERS: tuple[tuple[str, str], ...] = (
    (FILTER_ALL, "Barchasi"),
    (FILTER_TEST_STARTED, "Testni boshlaganlar"),
    (FILTER_TEST_COMPLETED, "Testni tugatganlar"),
    (FILTER_NOT_COMPLETED, "Tugatmaganlar"),
    (FILTER_PREMIUM, "Premium"),
    (FILTER_REFERRED, "Referral orqali kelganlar"),
)


@dataclass(frozen=True)
class TelegramUserFunnelStats:
    bot_entered: int
    test_started: int
    test_completed: int
    completion_rate: float
    premium_users: int


@dataclass(frozen=True)
class TelegramUserAdminRow:
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    status_label: str
    bot_started_at: datetime | None
    test_started_at: datetime | None
    test_completed_at: datetime | None
    mbti_type: str | None
    is_premium: bool
    premium_source: str | None
    referred: bool
    inviter_label: str | None
    session_id: int | None
    progress_reached: int
    progress_total: int
    progress_percent: float
    progress_status_label: str
    last_activity_at: datetime | None


@dataclass(frozen=True)
class ReferralInviteRow:
    index: int
    username: str | None
    first_name: str | None
    telegram_id: int | None
    completed: bool
    status_label: str


@dataclass(frozen=True)
class TelegramUserDetail:
    user: TelegramUser
    status_label: str
    test_started_at: datetime | None
    test_completed_at: datetime | None
    mbti_type: str | None
    is_premium: bool
    premium_source: str | None
    session_id: int | None
    inviter: TelegramUser | None
    progress_reached: int
    progress_total: int
    progress_percent: float
    progress_status_label: str
    last_activity_at: datetime | None
    referral_invites: list[ReferralInviteRow] = field(default_factory=list)


def _session_started(session: PersonalityTestSession | None) -> bool:
    if session is None:
        return False
    return session.started_at is not None or session.status not in (
        PersonalitySessionStatus.VISITED,
    )


def _resolve_premium_source(
    user: TelegramUser,
    session: PersonalityTestSession | None,
) -> str | None:
    if session is not None and session.premium_source:
        return session.premium_source
    if user.premium_source:
        return user.premium_source
    if session is not None and session.is_premium:
        return "payment"
    if session is not None and has_premium_access(session):
        return "referral"
    return None


def _status_label(user: TelegramUser, session: PersonalityTestSession | None) -> str:
    if session is not None and has_premium_access(session):
        return "Premium"
    if session is not None and session.status == PersonalitySessionStatus.COMPLETED:
        return "Testni tugatdi"
    if _session_started(session):
        return "Testni boshladi"
    if user.bot_started_at is not None:
        return "Botga kirdi"
    return "—"


def _inviter_label(db: Session, user: TelegramUser) -> tuple[bool, str | None]:
    referral = db.scalar(
        select(TelegramReferral).where(TelegramReferral.referred_telegram_user_id == user.id)
    )
    if referral is None:
        return False, None
    inviter = db.get(TelegramUser, referral.referrer_telegram_user_id)
    if inviter is None:
        return True, None
    if inviter.telegram_username:
        return True, f"@{inviter.telegram_username}"
    if inviter.telegram_first_name:
        return True, inviter.telegram_first_name
    return True, str(inviter.telegram_id)


def _build_row(db: Session, user: TelegramUser) -> TelegramUserAdminRow:
    session = primary_session_for_telegram_user(db, user.telegram_id)
    referred, inviter_label = _inviter_label(db, user)
    return TelegramUserAdminRow(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.telegram_username,
        first_name=user.telegram_first_name,
        last_name=user.telegram_last_name,
        phone_number=user.phone_number,
        status_label=_status_label(user, session),
        bot_started_at=user.bot_started_at,
        test_started_at=session.started_at if session else None,
        test_completed_at=session.completed_at if session else None,
        mbti_type=session.result_type if session else None,
        is_premium=has_premium_access(session) if session else False,
        premium_source=_resolve_premium_source(user, session),
        referred=referred,
        inviter_label=inviter_label,
        session_id=session.id if session else None,
        progress_reached=progress_reached(session) if session else 0,
        progress_total=progress_total(session) if session else 0,
        progress_percent=progress_percent(session) if session else 0.0,
        progress_status_label=progress_status_label(session),
        last_activity_at=session.last_activity_at if session else user.last_seen_at,
    )


class AdminTelegramUserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def funnel_stats(self) -> TelegramUserFunnelStats:
        bot_entered = self._count(
            select(func.count()).select_from(TelegramUser).where(TelegramUser.bot_started_at.is_not(None))
        )
        test_started = self._count(
            select(func.count(func.distinct(PersonalityTestSession.telegram_user_id)))
            .select_from(PersonalityTestSession)
            .where(
                PersonalityTestSession.telegram_user_id.is_not(None),
                or_(
                    PersonalityTestSession.started_at.is_not(None),
                    PersonalityTestSession.status != PersonalitySessionStatus.VISITED,
                ),
            )
        )
        test_completed = self._count(
            select(func.count(func.distinct(PersonalityTestSession.telegram_user_id)))
            .select_from(PersonalityTestSession)
            .where(
                PersonalityTestSession.telegram_user_id.is_not(None),
                PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
            )
        )
        premium_users = self._count_premium_telegram_users()
        rate = round(test_completed / test_started * 100, 1) if test_started else 0.0
        return TelegramUserFunnelStats(
            bot_entered=bot_entered,
            test_started=test_started,
            test_completed=test_completed,
            completion_rate=rate,
            premium_users=premium_users,
        )

    def list_page(
        self,
        *,
        filter_key: str = FILTER_ALL,
        page: int = 1,
        page_size: int | None = None,
    ) -> Page[TelegramUserAdminRow]:
        page_num = normalize_page(page)
        size = normalize_page_size(page_size)
        stmt = select(TelegramUser).order_by(
            TelegramUser.last_seen_at.desc().nullslast(),
            TelegramUser.created_at.desc(),
        )
        count_stmt = select(func.count()).select_from(TelegramUser)
        clauses = self._filter_clauses(filter_key)
        for clause in clauses:
            stmt = stmt.where(clause)
            count_stmt = count_stmt.where(clause)

        total = self._count(count_stmt)
        offset = (page_num - 1) * size
        users = list(self.db.scalars(stmt.offset(offset).limit(size)).all())
        items = [_build_row(self.db, user) for user in users]
        return Page(items=items, total=total, page=page_num, page_size=size)

    def get_detail(self, user_id: int) -> TelegramUserDetail | None:
        user = self.db.get(TelegramUser, user_id)
        if user is None:
            return None
        session = primary_session_for_telegram_user(self.db, user.telegram_id)
        inviter = None
        referral = self.db.scalar(
            select(TelegramReferral).where(TelegramReferral.referred_telegram_user_id == user.id)
        )
        if referral is not None:
            inviter = self.db.get(TelegramUser, referral.referrer_telegram_user_id)

        invites: list[ReferralInviteRow] = []
        for idx, ref in enumerate(list_referrals_for_referrer(self.db, user.id)[:3], start=1):
            referred = ref.referred
            ref_session = (
                primary_session_for_telegram_user(self.db, referred.telegram_id) if referred else None
            )
            status = _status_label(referred, ref_session) if referred else "—"
            invites.append(
                ReferralInviteRow(
                    index=idx,
                    username=referred.telegram_username if referred else None,
                    first_name=referred.telegram_first_name if referred else None,
                    telegram_id=referred.telegram_id if referred else None,
                    completed=ref.completed_at is not None,
                    status_label=status,
                )
            )

        return TelegramUserDetail(
            user=user,
            status_label=_status_label(user, session),
            test_started_at=session.started_at if session else None,
            test_completed_at=session.completed_at if session else None,
            mbti_type=session.result_type if session else None,
            is_premium=has_premium_access(session) if session else False,
            premium_source=_resolve_premium_source(user, session),
            session_id=session.id if session else None,
            inviter=inviter,
            progress_reached=progress_reached(session) if session else 0,
            progress_total=progress_total(session) if session else 0,
            progress_percent=progress_percent(session) if session else 0.0,
            progress_status_label=progress_status_label(session),
            last_activity_at=session.last_activity_at if session else user.last_seen_at,
            referral_invites=invites,
        )

    def _filter_clauses(self, filter_key: str) -> list:
        if filter_key == FILTER_TEST_STARTED:
            return [
                TelegramUser.telegram_id.in_(
                    select(PersonalityTestSession.telegram_user_id).where(
                        PersonalityTestSession.telegram_user_id.is_not(None),
                        or_(
                            PersonalityTestSession.started_at.is_not(None),
                            PersonalityTestSession.status != PersonalitySessionStatus.VISITED,
                        ),
                    )
                )
            ]
        if filter_key == FILTER_TEST_COMPLETED:
            return [
                TelegramUser.telegram_id.in_(
                    select(PersonalityTestSession.telegram_user_id).where(
                        PersonalityTestSession.telegram_user_id.is_not(None),
                        PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
                    )
                )
            ]
        if filter_key == FILTER_NOT_COMPLETED:
            started = select(PersonalityTestSession.telegram_user_id).where(
                PersonalityTestSession.telegram_user_id.is_not(None),
                or_(
                    PersonalityTestSession.started_at.is_not(None),
                    PersonalityTestSession.status != PersonalitySessionStatus.VISITED,
                ),
            )
            completed = select(PersonalityTestSession.telegram_user_id).where(
                PersonalityTestSession.telegram_user_id.is_not(None),
                PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
            )
            return [
                TelegramUser.telegram_id.in_(started),
                ~TelegramUser.telegram_id.in_(completed),
            ]
        if filter_key == FILTER_PREMIUM:
            now = utcnow()
            return [
                TelegramUser.telegram_id.in_(
                    select(PersonalityTestSession.telegram_user_id).where(
                        PersonalityTestSession.telegram_user_id.is_not(None),
                        or_(
                            PersonalityTestSession.is_premium.is_(True),
                            PersonalityTestSession.premium_until > now,
                        ),
                    )
                )
            ]
        if filter_key == FILTER_REFERRED:
            return [
                exists().where(TelegramReferral.referred_telegram_user_id == TelegramUser.id)
            ]
        return []

    def _count(self, stmt) -> int:
        return int(self.db.scalar(stmt) or 0)

    def _count_premium_telegram_users(self) -> int:
        now = utcnow()
        return self._count(
            select(func.count(func.distinct(PersonalityTestSession.telegram_user_id)))
            .select_from(PersonalityTestSession)
            .where(
                PersonalityTestSession.telegram_user_id.is_not(None),
                or_(
                    PersonalityTestSession.is_premium.is_(True),
                    PersonalityTestSession.premium_until > now,
                ),
            )
        )

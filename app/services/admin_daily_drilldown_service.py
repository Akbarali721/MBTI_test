"""Admin: kunlik tashrif/tugatish/tasdiqlash drill-down."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.payment_request import PAYMENT_STATUS_APPROVED, PaymentRequest
from app.models.personality import PersonalityTestSession
from app.models.telegram_user import TelegramReferral, TelegramUser
from app.personality.test_progress import progress_reached, progress_total
from app.services.premium_access import has_premium_access
from app.timeutils import TASHKENT_TZ, format_tashkent

METRIC_VISITED = "visited"
METRIC_COMPLETED = "completed"
METRIC_APPROVED = "approved"

METRIC_LABELS: dict[str, str] = {
    METRIC_VISITED: "Tashriflar",
    METRIC_COMPLETED: "Testni tugatganlar",
    METRIC_APPROVED: "Premium tasdiqlangan",
}


@dataclass(frozen=True)
class DailyDrilldownRow:
    session_id: int
    telegram_id: int | None
    username: str | None
    first_name: str | None
    last_name: str | None
    display_name: str
    visit_at: datetime | None
    test_started_at: datetime | None
    progress_reached: int
    progress_total: int
    max_question_reached: int
    completed_at: datetime | None
    is_premium: bool
    premium_source: str | None
    last_activity_at: datetime | None
    source: str | None
    referral_label: str | None
    status_label: str
    telegram_user_pk: int | None


@dataclass(frozen=True)
class DailyDrilldownReport:
    day_label: str
    metric: str
    metric_label: str
    total_sessions: int
    unique_users: int
    rows: list[DailyDrilldownRow]


def parse_tashkent_day(label: str) -> datetime:
    """YYYY-MM-DD → Toshkent kun boshining UTC lahzasi."""
    try:
        year, month, day = (int(part) for part in label.split("-", 2))
        local = datetime(year, month, day, tzinfo=TASHKENT_TZ)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid date") from exc
    return local.astimezone(timezone.utc)


def day_end(day_start: datetime) -> datetime:
    return day_start + timedelta(days=1)


def _session_status_label(session: PersonalityTestSession) -> str:
    anonymous = (
        session.telegram_user_id is None and not session.telegram_username and not session.telegram_first_name
    )
    if has_premium_access(session):
        return "Premium"
    if session.status == PersonalitySessionStatus.COMPLETED:
        return "Testni tugatdi"
    if session.started_at is not None or session.status not in (PersonalitySessionStatus.VISITED,):
        return "Testni boshladi"
    if anonymous:
        return "Anonymous web visit"
    return "Faqat tashrif"


def _display_name(
    session: PersonalityTestSession,
    tg_user: TelegramUser | None,
) -> str:
    username = (tg_user.telegram_username if tg_user else None) or session.telegram_username
    if username:
        return f"@{username}"
    first = (tg_user.telegram_first_name if tg_user else None) or session.telegram_first_name
    tg_id = session.telegram_user_id
    if first and tg_id:
        return f"{first} ({tg_id})"
    if first:
        return first
    if tg_id:
        return str(tg_id)
    return "Anonymous"


def _unique_key(session: PersonalityTestSession) -> str:
    if session.telegram_user_id is not None:
        return f"tg:{session.telegram_user_id}"
    if session.user_id is not None:
        return f"user:{session.user_id}"
    return f"session:{session.id}"


def _referral_label(db: Session, session: PersonalityTestSession, tg_user: TelegramUser | None) -> str | None:
    if session.referred_by_session_id is not None:
        return f"Sessiya #{session.referred_by_session_id}"
    if tg_user is None:
        return None
    referral = db.scalar(
        select(TelegramReferral).where(TelegramReferral.referred_telegram_user_id == tg_user.id)
    )
    if referral is None:
        return None
    inviter = db.get(TelegramUser, referral.referrer_telegram_user_id)
    if inviter is None:
        return "Referral"
    if inviter.telegram_username:
        return f"@{inviter.telegram_username}"
    if inviter.telegram_first_name:
        return inviter.telegram_first_name
    return str(inviter.telegram_id)


class AdminDailyDrilldownService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def report(
        self,
        *,
        day_label: str,
        metric: str,
        variant: str | None = None,
    ) -> DailyDrilldownReport | None:
        if metric not in METRIC_LABELS:
            return None
        try:
            start = parse_tashkent_day(day_label)
        except ValueError:
            return None
        end = day_end(start)
        sessions = self._sessions_for_metric(metric=metric, start=start, end=end, variant=variant)
        tg_users = self._telegram_users_for_sessions(sessions)
        rows: list[DailyDrilldownRow] = []
        unique_keys: set[str] = set()
        for session in sessions:
            tg_user = tg_users.get(session.telegram_user_id) if session.telegram_user_id else None
            unique_keys.add(_unique_key(session))
            rows.append(
                DailyDrilldownRow(
                    session_id=session.id,
                    telegram_id=session.telegram_user_id,
                    username=(tg_user.telegram_username if tg_user else None) or session.telegram_username,
                    first_name=(
                        (tg_user.telegram_first_name if tg_user else None) or session.telegram_first_name
                    ),
                    last_name=(tg_user.telegram_last_name if tg_user else None) or session.telegram_last_name,
                    display_name=_display_name(session, tg_user),
                    visit_at=session.created_at,
                    test_started_at=session.started_at,
                    progress_reached=progress_reached(session),
                    progress_total=progress_total(session),
                    max_question_reached=session.max_question_reached,
                    completed_at=session.completed_at,
                    is_premium=has_premium_access(session),
                    premium_source=session.premium_source or (tg_user.premium_source if tg_user else None),
                    last_activity_at=session.last_activity_at,
                    source=session.source,
                    referral_label=_referral_label(self.db, session, tg_user),
                    status_label=_session_status_label(session),
                    telegram_user_pk=tg_user.id if tg_user else None,
                )
            )
        return DailyDrilldownReport(
            day_label=day_label,
            metric=metric,
            metric_label=METRIC_LABELS[metric],
            total_sessions=len(rows),
            unique_users=len(unique_keys),
            rows=rows,
        )

    def _sessions_for_metric(
        self,
        *,
        metric: str,
        start: datetime,
        end: datetime,
        variant: str | None,
    ) -> list[PersonalityTestSession]:
        model = PersonalityTestSession
        stmt = select(model)
        if metric == METRIC_VISITED:
            stmt = stmt.where(model.created_at >= start, model.created_at < end)
        elif metric == METRIC_COMPLETED:
            stmt = stmt.where(
                model.status == PersonalitySessionStatus.COMPLETED,
                model.completed_at.is_not(None),
                model.completed_at >= start,
                model.completed_at < end,
            )
        else:
            approved_session_ids = select(PaymentRequest.session_id).where(
                PaymentRequest.status == PAYMENT_STATUS_APPROVED,
                PaymentRequest.approved_at.is_not(None),
                PaymentRequest.approved_at >= start,
                PaymentRequest.approved_at < end,
            )
            stmt = stmt.where(
                or_(
                    and_(
                        model.premium_approved_at.is_not(None),
                        model.premium_approved_at >= start,
                        model.premium_approved_at < end,
                    ),
                    model.id.in_(approved_session_ids),
                )
            )
        if variant:
            stmt = stmt.where(model.variant == variant)
        stmt = stmt.order_by(
            model.created_at.desc()
            if metric == METRIC_VISITED
            else model.last_activity_at.desc().nullslast(),
            model.id.desc(),
        )
        return list(self.db.scalars(stmt).all())

    def _telegram_users_for_sessions(self, sessions: list[PersonalityTestSession]) -> dict[int, TelegramUser]:
        ids = {session.telegram_user_id for session in sessions if session.telegram_user_id is not None}
        if not ids:
            return {}
        rows = self.db.scalars(select(TelegramUser).where(TelegramUser.telegram_id.in_(ids))).all()
        return {row.telegram_id: row for row in rows}


def format_dt(value: datetime | None) -> str:
    return format_tashkent(value) or "—"

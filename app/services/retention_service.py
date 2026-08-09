"""Ma'lumotlarni saqlash siyosati.

Uchta qat'iy qoida butun modulni belgilaydi:

1. **Pul izi hech qachon o'chirilmaydi.** `payment_requests.session_id` da
   `ON DELETE CASCADE` bor, ya'ni sessiyani o'chirish TO'LOV QATORINI ham o'chiradi.
   Shuning uchun "to'lovlarga tegmaymiz" degan va'da yetarli emas — nomzod so'rovining
   O'ZIDA `NOT EXISTS (payment_requests ...)` sharti turadi va o'chirishdan oldin
   yana bir marta sanab tekshiriladi.
2. **Voronka buzilmaydi.** O'chiriladigan qatorlar avval `session_daily_stats` ga
   yig'iladi, shundan keyingina o'chiriladi.
3. **Tugallanmagan sessiyalar o'chirilmaydi, ANONIMLASHTIRILADI.** Shaxsiy ma'lumot
   (javoblar, Telegram identifikatori) yo'qoladi, qator esa hisobotda qoladi.

Buzg'unchi amallar ATAYLAB faqat CLI da (`python -m app.retention --apply`). Admin
panelida faqat "nima o'chiriladi" hisoboti ko'rinadi: shunda HTTP so'rov ichida uzoq
davom etadigan, ikki marta bosilishi mumkin bo'lgan va proksi timeoutida qayta
yuboriladigan o'chirish umuman bo'lmaydi.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.authz import AdminIdentity
from app.config import settings
from app.models.admin import AdminAuditLog
from app.models.analytics import SessionDailyStats
from app.models.enums import NOTIFICATION_TERMINAL_STATUSES, PersonalitySessionStatus
from app.models.notification import NotificationOutbox
from app.models.payment_request import PaymentRequest
from app.models.personality import PersonalityAnswer, PersonalityTestSession
from app.models.team import TeamMember
from app.services import audit_service
from app.services.admin_analytics_service import STAGE_KEYS, payment_rollup, session_stage_depth
from app.timeutils import tashkent_day_start, utcnow

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
# Bitta yurishda o'chiriladigan qatorlarning yuqori chegarasi — uzoq tranzaksiya
# va kutilmagan katta ta'sirning oldini oladi.
DEFAULT_MAX_ROWS = 50_000

RULE_VISITED = "visited"
RULE_INCOMPLETE = "incomplete"
RULE_OUTBOX = "outbox"
RULE_AUDIT = "audit"

RULE_ORDER: tuple[str, ...] = (RULE_VISITED, RULE_INCOMPLETE, RULE_OUTBOX, RULE_AUDIT)

RULE_LABELS: dict[str, str] = {
    RULE_VISITED: "Boshlanmagan sessiyalar (o'chiriladi)",
    RULE_INCOMPLETE: "Tugallanmagan sessiyalar (anonimlashtiriladi)",
    RULE_OUTBOX: "Yakunlangan bildirishnomalar (o'chiriladi)",
    RULE_AUDIT: "Audit jurnalining oddiy yozuvlari (o'chiriladi)",
}


@dataclass(frozen=True)
class RuleReport:
    rule: str
    days: int | None
    cutoff: datetime | None
    candidates: int = 0
    affected: int = 0
    skipped_reason: str | None = None

    @property
    def enabled(self) -> bool:
        return self.days is not None


@dataclass
class RetentionReport:
    run_id: str
    dry_run: bool
    started_at: datetime
    rules: list[RuleReport] = field(default_factory=list)

    @property
    def total_affected(self) -> int:
        return sum(rule.affected for rule in self.rules)

    @property
    def total_candidates(self) -> int:
        return sum(rule.candidates for rule in self.rules)


# --- Nomzodlarni tanlash ---


def _session_safety_clauses() -> list:
    """Sessiyani tegib bo'lmaydigan qiladigan har qanday belgi.

    SQL darajasida: Python tomonidagi filtr bitta yo'lni o'tkazib yuborsa, natija
    to'lov qatorining kaskad bilan o'chishi bo'lardi.
    """
    model = PersonalityTestSession
    has_payment = select(PaymentRequest.id).where(PaymentRequest.session_id == model.id).exists()
    in_team = select(TeamMember.id).where(TeamMember.session_id == model.id).exists()
    return [
        ~has_payment,
        ~in_team,
        model.is_premium.is_(False),
        # Referal mukofoti bergan vaqtli premium ham "tegib bo'lmaydi" belgisi.
        # Amalda mukofot faqat TUGATILGAN sessiyaga tushadi va qoidalar unga
        # baribir tegmasdi, lekin bu ro'yxat mudofaaning oxirgi qatori.
        # `referred_by_session_id` ataylab YO'Q: havolani bosib kirgan-u testni
        # boshlamagan sessiya oddiy tashrif bilan bir xil tozalanadi, aks holda
        # jadval tashlab ketilgan referal tashriflari bilan cheksiz o'sardi.
        model.premium_until.is_(None),
        model.premium_requested.is_(False),
        model.premium_requested_at.is_(None),
        model.premium_approved_at.is_(None),
        model.completed_at.is_(None),
        model.result_type.is_(None),
    ]


def _stale_visited_stmt(cutoff: datetime):
    model = PersonalityTestSession
    activity = func.coalesce(model.last_activity_at, model.created_at)
    return (
        select(model.id)
        .where(
            model.status == PersonalitySessionStatus.VISITED,
            activity < cutoff,
            *_session_safety_clauses(),
        )
        .order_by(model.id)
    )


def stale_visited_ids(db: Session, *, cutoff: datetime, limit: int | None = None) -> list[int]:
    """Hech qachon boshlanmagan va eskirgan sessiyalar."""
    stmt = _stale_visited_stmt(cutoff)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def _stale_incomplete_stmt(cutoff: datetime):
    model = PersonalityTestSession
    activity = func.coalesce(model.last_activity_at, model.created_at)
    return (
        select(model.id)
        .where(
            model.status.in_((PersonalitySessionStatus.STARTED, PersonalitySessionStatus.IN_PROGRESS)),
            activity < cutoff,
            model.anonymized_at.is_(None),
            *_session_safety_clauses(),
        )
        .order_by(model.id)
    )


def stale_incomplete_ids(db: Session, *, cutoff: datetime, limit: int | None = None) -> list[int]:
    """Boshlangan, lekin tugallanmagan va tashlab ketilgan sessiyalar."""
    stmt = _stale_incomplete_stmt(cutoff)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def count_stale_visited(db: Session, *, cutoff: datetime) -> int:
    return _count(db, _stale_visited_stmt(cutoff))


def count_stale_incomplete(db: Session, *, cutoff: datetime) -> int:
    return _count(db, _stale_incomplete_stmt(cutoff))


def _count(db: Session, stmt) -> int:
    return int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)


def _assert_no_financial_rows(db: Session, ids: list[int]) -> None:
    """O'chirishdan oldingi oxirgi to'siq.

    Kaskad jim ishlaydi, shuning uchun "bo'lmasligi kerak" degan holat aniqlansa
    ish davom etmaydi.
    """
    if not ids:
        return
    payments = int(
        db.scalar(select(func.count()).select_from(PaymentRequest).where(PaymentRequest.session_id.in_(ids)))
        or 0
    )
    members = int(
        db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.session_id.in_(ids))) or 0
    )
    if payments or members:
        raise RuntimeError(
            f"Saqlash siyosati to'xtatildi: nomzodlar orasida to'lov ({payments}) yoki "
            f"jamoa a'zosi ({members}) bor"
        )


# --- Agregat ---


def rollup_sessions(db: Session, ids: list[int]) -> int:
    """O'chirishdan oldin sessiyalarni kunlik agregatga qo'shadi."""
    if not ids:
        return 0
    model = PersonalityTestSession
    payments = payment_rollup()
    depth = session_stage_depth(payments)
    rows = db.execute(
        select(model.created_at, model.variant, depth, func.count())
        .select_from(model)
        .outerjoin(payments, payments.c.session_id == model.id)
        .where(model.id.in_(ids))
        .group_by(model.created_at, model.variant, depth)
    ).all()

    # (kun, to'plam) -> bosqichlar bo'yicha kumulyativ sonlar
    buckets: dict[tuple[datetime, str], list[int]] = {}
    for created_at, variant, stage_depth, count in rows:
        day = tashkent_day_start(created_at)
        bucket = buckets.setdefault((day, variant), [0] * len(STAGE_KEYS))
        # Chuqurlik `d` bo'lgan sessiya 0..d bosqichlarining HAMMASIDA hisoblanadi.
        for index in range(int(stage_depth or 0) + 1):
            bucket[index] += int(count or 0)

    now = utcnow()
    for (day, variant), values in buckets.items():
        existing = db.scalar(
            select(SessionDailyStats).where(
                SessionDailyStats.day == day, SessionDailyStats.variant == variant
            )
        )
        if existing is None:
            db.add(
                SessionDailyStats(
                    day=day,
                    variant=variant,
                    updated_at=now,
                    **{key: values[index] for index, key in enumerate(STAGE_KEYS)},
                )
            )
            continue
        for index, key in enumerate(STAGE_KEYS):
            setattr(existing, key, getattr(existing, key) + values[index])
        existing.updated_at = now
    db.flush()
    return len(buckets)


# --- Anonimlashtirish ---


def anonymize_sessions(db: Session, ids: list[int]) -> int:
    """Javoblar va shaxsiy maydonlarni tozalaydi, qatorni saqlab qoladi.

    `token` NULL qilinmaydi (ustun NOT NULL va noyob), balki yangi qiymatga
    almashtiriladi — eski havola shundan keyin hech narsani ochmaydi.
    """
    if not ids:
        return 0
    db.execute(delete(PersonalityAnswer).where(PersonalityAnswer.session_id.in_(ids)))

    now = utcnow()
    updated = 0
    for session in db.scalars(select(PersonalityTestSession).where(PersonalityTestSession.id.in_(ids))).all():
        session.token = uuid.uuid4().hex
        session.payment_code = None
        session.share_code = None
        session.user_id = None
        session.telegram_user_id = None
        session.telegram_username = None
        session.telegram_first_name = None
        session.result_type = None
        session.answered_questions = 0
        session.current_question_index = 0
        for key in ("e", "i", "s", "n", "t", "f", "j", "p"):
            setattr(session, f"{key}_score", 0)
        session.anonymized_at = now
        updated += 1
    db.flush()
    return updated


# --- Qoidalar ---


def _cutoff(days: int | None) -> datetime | None:
    return utcnow() - timedelta(days=days) if days else None


def _visited_rule(db: Session, *, dry_run: bool, max_rows: int, days: int | None) -> RuleReport:
    cutoff = _cutoff(days)
    if cutoff is None:
        return RuleReport(rule=RULE_VISITED, days=None, cutoff=None, skipped_reason="off")

    # Sanash uchun COUNT: quruq hisobot admin sahifasida ochiladi va u yerda
    # yuz minglab ID ni Python ro'yxatiga tortib olishning ma'nosi yo'q.
    candidates = count_stale_visited(db, cutoff=cutoff)
    if dry_run:
        return RuleReport(rule=RULE_VISITED, days=days, cutoff=cutoff, candidates=candidates)

    removed = 0
    while removed < max_rows:
        batch = stale_visited_ids(db, cutoff=cutoff, limit=min(BATCH_SIZE, max_rows - removed))
        if not batch:
            break
        _assert_no_financial_rows(db, batch)
        rollup_sessions(db, batch)
        db.execute(delete(PersonalityTestSession).where(PersonalityTestSession.id.in_(batch)))
        db.commit()
        removed += len(batch)
    return RuleReport(rule=RULE_VISITED, days=days, cutoff=cutoff, candidates=candidates, affected=removed)


def _incomplete_rule(db: Session, *, dry_run: bool, max_rows: int, days: int | None) -> RuleReport:
    cutoff = _cutoff(days)
    if cutoff is None:
        return RuleReport(rule=RULE_INCOMPLETE, days=None, cutoff=None, skipped_reason="off")

    candidates = count_stale_incomplete(db, cutoff=cutoff)
    if dry_run:
        return RuleReport(rule=RULE_INCOMPLETE, days=days, cutoff=cutoff, candidates=candidates)

    changed = 0
    while changed < max_rows:
        batch = stale_incomplete_ids(db, cutoff=cutoff, limit=min(BATCH_SIZE, max_rows - changed))
        if not batch:
            break
        _assert_no_financial_rows(db, batch)
        changed += anonymize_sessions(db, batch)
        db.commit()
    return RuleReport(rule=RULE_INCOMPLETE, days=days, cutoff=cutoff, candidates=candidates, affected=changed)


def _outbox_rule(db: Session, *, dry_run: bool, max_rows: int, days: int | None) -> RuleReport:
    cutoff = _cutoff(days)
    if cutoff is None:
        return RuleReport(rule=RULE_OUTBOX, days=None, cutoff=None, skipped_reason="off")

    # `created_at` emas, `finished_at`: yetkazilmagan (pending/sending) xabar hech
    # qachon o'chirilmaydi, u qancha eski bo'lsa ham — aynan o'sha qator "mijozga
    # xabar berilmagan" degan yagona dalil.
    condition = (
        NotificationOutbox.status.in_(tuple(NOTIFICATION_TERMINAL_STATUSES)),
        NotificationOutbox.finished_at.is_not(None),
        NotificationOutbox.finished_at < cutoff,
    )
    candidates = int(db.scalar(select(func.count()).select_from(NotificationOutbox).where(*condition)) or 0)
    if dry_run:
        return RuleReport(rule=RULE_OUTBOX, days=days, cutoff=cutoff, candidates=candidates)

    ids = list(db.scalars(select(NotificationOutbox.id).where(*condition).limit(max_rows)).all())
    if ids:
        db.execute(delete(NotificationOutbox).where(NotificationOutbox.id.in_(ids)))
        db.commit()
    return RuleReport(rule=RULE_OUTBOX, days=days, cutoff=cutoff, candidates=candidates, affected=len(ids))


def _audit_rule(db: Session, *, dry_run: bool, max_rows: int, days: int | None) -> RuleReport:
    cutoff = _cutoff(days)
    if cutoff is None:
        return RuleReport(rule=RULE_AUDIT, days=None, cutoff=None, skipped_reason="off")

    # Pul, rol, eksport va saqlash siyosatiga tegishli yozuvlar hech qachon
    # tozalanmaydi — muddat sozlamasi qanchalik qisqa bo'lsa ham.
    condition = (
        AdminAuditLog.created_at < cutoff,
        AdminAuditLog.action.not_in(tuple(audit_service.NEVER_PURGED_ACTIONS)),
    )
    candidates = int(db.scalar(select(func.count()).select_from(AdminAuditLog).where(*condition)) or 0)
    if dry_run:
        return RuleReport(rule=RULE_AUDIT, days=days, cutoff=cutoff, candidates=candidates)

    ids = list(db.scalars(select(AdminAuditLog.id).where(*condition).limit(max_rows)).all())
    if ids:
        db.execute(delete(AdminAuditLog).where(AdminAuditLog.id.in_(ids)))
        db.commit()
    return RuleReport(rule=RULE_AUDIT, days=days, cutoff=cutoff, candidates=candidates, affected=len(ids))


_RULES = {
    RULE_VISITED: _visited_rule,
    RULE_INCOMPLETE: _incomplete_rule,
    RULE_OUTBOX: _outbox_rule,
    RULE_AUDIT: _audit_rule,
}


def run(
    db: Session,
    *,
    dry_run: bool = True,
    rules: Iterable[str] | None = None,
    max_rows: int = DEFAULT_MAX_ROWS,
    actor: AdminIdentity | None = None,
    days_override: dict[str, int] | None = None,
) -> RetentionReport:
    """Siyosatni bajaradi (yoki faqat hisobot beradi).

    `days_override` — sozlamadagi muddatni almashtiradi (eski
    `python -m app.seed --purge-visited --days N` buyrug'i uchun).
    """
    selected = tuple(rules) if rules else RULE_ORDER
    unknown = [rule for rule in selected if rule not in _RULES]
    if unknown:
        raise ValueError(f"Noma'lum qoida: {', '.join(unknown)}")

    report = RetentionReport(run_id=uuid.uuid4().hex[:12], dry_run=dry_run, started_at=utcnow())
    for rule in RULE_ORDER:
        if rule not in selected:
            continue
        days = (days_override or {}).get(rule, settings.retention_days(rule))
        report.rules.append(_RULES[rule](db, dry_run=dry_run, max_rows=max_rows, days=days))

    if not dry_run:
        audit_service.record(
            db,
            actor,
            audit_service.RETENTION_RUN,
            detail={
                "run": report.run_id,
                **{item.rule: f"{item.affected}/{item.candidates}" for item in report.rules},
            },
        )
        db.commit()
        logger.info("Saqlash siyosati bajarildi: run=%s, jami=%s", report.run_id, report.total_affected)
    return report


def mark_heartbeat(db: Session, report: RetentionReport) -> None:
    from app.models.notification import RETENTION_HEARTBEAT
    from app.services.notification_outbox import touch_heartbeat

    touch_heartbeat(db, RETENTION_HEARTBEAT, detail=f"{report.run_id}: {report.total_affected} qator")

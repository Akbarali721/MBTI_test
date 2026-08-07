"""Bildirishnoma navbati bilan ishlash: yozish, olish va yakunlash.

Yuborishning o'zi `app/bot/outbox_worker.py` da — bu modul Telegramni bilmaydi va
shuning uchun veb jarayonidan ham bemalol ishlatiladi.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import Table, and_, case, func, or_, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import NOTIFICATION_TERMINAL_STATUSES, NotificationStatus
from app.models.notification import NotificationOutbox, ServiceHeartbeat
from app.timeutils import as_utc, utcnow

logger = logging.getLogger(__name__)

# --- Xabar turlari ---
ADMIN_RECEIPT = "admin_receipt"
USER_APPROVED = "user_approved"
USER_REJECTED = "user_rejected"
PREMIUM_PDF = "premium_pdf"

KNOWN_KINDS: frozenset[str] = frozenset({ADMIN_RECEIPT, USER_APPROVED, USER_REJECTED, PREMIUM_PDF})

# `params` shakli o'zgarsa oshiriladi. Eski ishchi kattaroq versiyani ko'rsa qatorni
# terminal qilmaydi — deploy'ni orqaga qaytarish navbatni yo'q qilmasligi kerak.
SCHEMA_VERSION = 1

BASE_BACKOFF_SECONDS = 30
MAX_BACKOFF_SECONDS = 3600
_JITTER = 0.2
# Flood-limit urinishni "bepul" qilish faqat shu muddat ichida. Undan keyin
# urinishlar hisoblanadi va qator oxir-oqibat yakunlanadi.
REFUND_WINDOW_SECONDS = 24 * 3600


def event_stamp(moment: datetime | None) -> str:
    """dedup_key uchun hodisa lahzasi.

    Kalitga aynan shu qism kiradi: bitta to'lovga TUZATILGAN chek kelsa, qator ID si
    o'zgarmaydi va faqat `receipt_sent_at` yangilanadi — vaqtsiz kalit ikkinchi
    (o'qiladigan) chekni jimgina yutib yuborardi.

    Aniqlik millisekundda: xira chekdan keyin darhol yuborilgan aniqrog'i ham
    alohida hodisa bo'lishi kerak.
    """
    resolved = as_utc(moment) or utcnow()
    return str(int(resolved.timestamp() * 1000))


def dedup_key(kind: str, chat_id: int, target_id: int, stamp: str) -> str:
    return f"{kind}:{chat_id}:{target_id}:{stamp}"


def enqueue(
    db: Session,
    *,
    kind: str,
    chat_id: int,
    params: dict[str, Any],
    key: str,
    max_attempts: int | None = None,
) -> None:
    """Navbatga qator qo'shadi (chaqiruvchining tranzaksiyasida).

    Takroriy kalit HECH QACHON IntegrityError bermaydi: bu chaqiruv to'lov holatini
    o'zgartirgan tranzaksiya ichida bajariladi va istisno o'sha o'zgarishni ham
    orqaga qaytarib yuborardi.
    """
    now = utcnow()
    values = {
        "kind": kind,
        "chat_id": chat_id,
        "params": params,
        "schema_version": SCHEMA_VERSION,
        "status": NotificationStatus.PENDING.value,
        "attempts": 0,
        "max_attempts": max_attempts or settings.outbox_max_attempts,
        "dedup_key": key,
        "next_attempt_at": now,
        "created_at": now,
    }

    table = cast(Table, NotificationOutbox.__table__)
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt: Any = sqlite_insert(table).values(**values)
    elif dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(table).values(**values)
    else:
        if db.scalar(select(NotificationOutbox.id).where(NotificationOutbox.dedup_key == key)) is None:
            db.add(NotificationOutbox(**values))
        return

    db.execute(stmt.on_conflict_do_nothing(index_elements=[table.c.dedup_key]))


# --- Ishchi uchun ---


def reclaim_stale(db: Session, *, now: datetime | None = None) -> int:
    """Ijarasi tugagan 'sending' qatorlarni qaytadan navbatga qo'yadi.

    Urinish hisobi QAYTARILADI: `claim_batch` uni band qilish paytida oshiradi, lekin
    jarayon yuborishga yetmasdan o'lgan bo'lsa hech qanday urinish bo'lmagan. Aks holda
    bir necha qayta ishga tushish yoki noto'g'ri BOT_TOKEN sababli aylanish hech qachon
    yuborilmagan xabarning butun byudjetini yeb qo'yardi.
    """
    moment = now or utcnow()
    stmt = (
        update(NotificationOutbox)
        .where(
            NotificationOutbox.status == NotificationStatus.SENDING.value,
            NotificationOutbox.lease_expires_at.is_not(None),
            NotificationOutbox.lease_expires_at < moment,
        )
        .values(
            status=NotificationStatus.PENDING.value,
            attempts=_refunded_attempts(),
            claimed_by=None,
            lease_expires_at=None,
        )
    )
    result = db.execute(stmt)
    db.commit()
    return int(getattr(result, "rowcount", 0) or 0)


def _refunded_attempts() -> Any:
    """Band qilishda oshirilgan urinishni qaytaradi (0 dan pastga tushmaydi)."""
    return case(
        (NotificationOutbox.attempts > 0, NotificationOutbox.attempts - 1),
        else_=0,
    )


def claim_batch(
    db: Session,
    *,
    worker_id: str,
    limit: int,
    now: datetime | None = None,
    lease_seconds: int | None = None,
) -> list[int]:
    """Yuborishga tayyor qatorlarni band qiladi va ID larini qaytaradi.

    Band qilish `UPDATE ... WHERE status='pending'` (compare-and-swap) orqali:
    `SELECT FOR UPDATE SKIP LOCKED` SQLite'da yo'q, ya'ni production yo'li testlarda
    umuman ishlamas edi. CAS ikkala dialektda ham bir xil to'g'ri.
    """
    moment = now or utcnow()
    lease = timedelta(seconds=lease_seconds or settings.outbox_lease_seconds)
    candidates = list(
        db.scalars(
            select(NotificationOutbox.id)
            .where(
                NotificationOutbox.status == NotificationStatus.PENDING.value,
                NotificationOutbox.next_attempt_at <= moment,
            )
            .order_by(NotificationOutbox.id)
            .limit(limit)
        ).all()
    )

    claimed: list[int] = []
    for row_id in candidates:
        result = db.execute(
            update(NotificationOutbox)
            .where(
                NotificationOutbox.id == row_id,
                NotificationOutbox.status == NotificationStatus.PENDING.value,
            )
            .values(
                status=NotificationStatus.SENDING.value,
                attempts=NotificationOutbox.attempts + 1,
                claimed_by=worker_id[:64],
                lease_expires_at=moment + lease,
            )
        )
        if getattr(result, "rowcount", 0) == 1:
            claimed.append(row_id)
    db.commit()
    return claimed


def get_row(db: Session, row_id: int) -> NotificationOutbox | None:
    return db.get(NotificationOutbox, row_id)


def mark_sent(db: Session, row_id: int) -> None:
    _finish(db, row_id, NotificationStatus.SENT.value, error=None)


def mark_terminal(db: Session, row_id: int, status: str, *, error: str | None = None) -> None:
    _finish(db, row_id, status, error=error)


def _finish(db: Session, row_id: int, status: str, *, error: str | None) -> None:
    if status not in NOTIFICATION_TERMINAL_STATUSES:
        raise ValueError(f"Terminal bo'lmagan holat: {status}")
    db.execute(
        update(NotificationOutbox)
        .where(NotificationOutbox.id == row_id)
        .values(
            status=status,
            finished_at=utcnow(),
            lease_expires_at=None,
            claimed_by=None,
            last_error=(error or None) and error[:500],
        )
    )
    db.commit()


def backoff_delay(attempts: int) -> float:
    """Eksponensial kechikish + tasodifiy siljish.

    Siljishsiz Telegram uzilishidan keyin barcha qatorlar bir lahzada qayta urinadi.
    """
    step = min(BASE_BACKOFF_SECONDS * (2 ** max(0, attempts - 1)), MAX_BACKOFF_SECONDS)
    return step * (1 + random.uniform(-_JITTER, _JITTER))


def _within_refund_window(row: NotificationOutbox) -> bool:
    created = as_utc(row.created_at) or utcnow()
    return (utcnow() - created) < timedelta(seconds=REFUND_WINDOW_SECONDS)


def schedule_retry(
    db: Session,
    row_id: int,
    *,
    delay_seconds: float,
    error: str | None,
    refund_attempt: bool = False,
) -> None:
    """Qatorni keyinroqqa suradi.

    `refund_attempt` — Telegram o'zi "shuncha kutib turing" degan holat uchun:
    flood-limit urinishlar byudjetini yeb qo'ymasligi kerak. Lekin qaytarish
    CHEKSIZ emas: aks holda uzluksiz flood-limitda qator urinishlar sonini
    hech qachon tugatmasdan abadiy aylanaverardi.
    """
    row = db.get(NotificationOutbox, row_id)
    if row is None:
        return
    refund = refund_attempt and _within_refund_window(row)
    attempts = max(0, row.attempts - 1) if refund else row.attempts
    exhausted = not refund and attempts >= row.max_attempts
    row.attempts = attempts
    row.last_error = (error or None) and error[:500]
    row.claimed_by = None
    row.lease_expires_at = None
    if exhausted:
        row.status = NotificationStatus.FAILED.value
        row.finished_at = utcnow()
    else:
        row.status = NotificationStatus.PENDING.value
        row.next_attempt_at = utcnow() + timedelta(seconds=max(1.0, delay_seconds))
    db.commit()


def release_all_claimed(db: Session, worker_id: str) -> int:
    """Jarayon to'xtaganda band qilingan qatorlarni qaytaradi.

    Urinish hisobi `reclaim_stale` bilan bir xil sababdan qaytariladi: bu yo'lga
    to'xtatish yoki jarayon darajasidagi xato (masalan noto'g'ri BOT_TOKEN) olib
    keladi, ya'ni yuborishga urinish bo'lmagan.
    """
    result = db.execute(
        update(NotificationOutbox)
        .where(
            NotificationOutbox.status == NotificationStatus.SENDING.value,
            NotificationOutbox.claimed_by == worker_id[:64],
        )
        .values(
            status=NotificationStatus.PENDING.value,
            attempts=_refunded_attempts(),
            claimed_by=None,
            lease_expires_at=None,
        )
    )
    db.commit()
    return int(getattr(result, "rowcount", 0) or 0)


def retry_now(db: Session, row_id: int) -> bool:
    """Admin paneldagi "qayta urinish" tugmasi.

    Urinishlar hisobi nolga qaytariladi, aks holda qator darhol yana "failed" bo'lardi
    va tugma buzilgandek ko'rinardi.
    """
    row = db.get(NotificationOutbox, row_id)
    if row is None or row.status == NotificationStatus.SENT.value:
        return False
    row.status = NotificationStatus.PENDING.value
    row.attempts = 0
    row.next_attempt_at = utcnow()
    row.lease_expires_at = None
    row.claimed_by = None
    row.finished_at = None
    row.last_error = None
    db.flush()
    return True


# --- Admin paneli ---

ADMIN_STATUS_FILTERS: tuple[str, ...] = (
    "all",
    NotificationStatus.PENDING.value,
    NotificationStatus.SENDING.value,
    NotificationStatus.FAILED.value,
    NotificationStatus.BLOCKED.value,
    NotificationStatus.SENT.value,
    NotificationStatus.CANCELLED.value,
    NotificationStatus.INVALID.value,
)


def list_for_admin(
    db: Session,
    *,
    status_filter: str = "pending",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[NotificationOutbox], int]:
    stmt = select(NotificationOutbox)
    count_stmt = select(func.count()).select_from(NotificationOutbox)
    if status_filter and status_filter != "all":
        stmt = stmt.where(NotificationOutbox.status == status_filter)
        count_stmt = count_stmt.where(NotificationOutbox.status == status_filter)
    stmt = stmt.order_by(NotificationOutbox.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all()), int(db.scalar(count_stmt) or 0)


# --- Yurak urishi va ko'rsatkichlar ---


def touch_heartbeat(db: Session, name: str, *, detail: str | None = None) -> None:
    row = db.get(ServiceHeartbeat, name)
    if row is None:
        db.add(ServiceHeartbeat(name=name, seen_at=utcnow(), detail=detail))
    else:
        row.seen_at = utcnow()
        row.detail = detail
    db.commit()


def heartbeat_seen_at(db: Session, name: str) -> datetime | None:
    row = db.get(ServiceHeartbeat, name)
    return as_utc(row.seen_at) if row else None


@dataclass(frozen=True)
class OutboxHealth:
    counts: dict[str, int]
    oldest_pending_at: datetime | None
    overdue_pending: int
    unknown_kinds: int
    worker_seen_at: datetime | None

    @property
    def pending(self) -> int:
        return self.counts.get(NotificationStatus.PENDING.value, 0)

    @property
    def failed(self) -> int:
        return self.counts.get(NotificationStatus.FAILED.value, 0)


def health(db: Session, *, worker_seen_at: datetime | None = None) -> OutboxHealth:
    counts = {
        str(status): int(total or 0)
        for status, total in db.execute(
            select(NotificationOutbox.status, func.count()).group_by(NotificationOutbox.status)
        ).all()
    }
    waiting = or_(
        NotificationOutbox.status == NotificationStatus.PENDING.value,
        NotificationOutbox.status == NotificationStatus.SENDING.value,
    )
    oldest = as_utc(db.scalar(select(func.min(NotificationOutbox.created_at)).where(waiting)))
    overdue_before = utcnow() - timedelta(minutes=settings.outbox_overdue_minutes)
    overdue = int(
        db.scalar(
            select(func.count())
            .select_from(NotificationOutbox)
            .where(and_(waiting, NotificationOutbox.created_at < overdue_before))
        )
        or 0
    )
    unknown = int(
        db.scalar(
            select(func.count())
            .select_from(NotificationOutbox)
            .where(waiting, NotificationOutbox.kind.not_in(tuple(KNOWN_KINDS)))
        )
        or 0
    )
    return OutboxHealth(
        counts=counts,
        oldest_pending_at=oldest,
        overdue_pending=overdue,
        unknown_kinds=unknown,
        worker_seen_at=worker_seen_at,
    )

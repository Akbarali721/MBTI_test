"""Bildirishnoma navbati (outbox) va xizmat yurak urishi.

Nima uchun kerak: avval xabar to'g'ridan-to'g'ri Telegramga yuborilardi va yuborilmasa
IZSIZ yo'qolardi — mijoz botni bloklagan bo'lsa, tarmoq uzilsa yoki bot konteyneri
qayta ishga tushsa. Bundan tashqari veb paneldan tasdiqlanganda mijozga UMUMAN xabar
bormasdi, chunki veb jarayonida Bot obyekti yo'q.

Endi har xabar avval shu jadvalga yoziladi (holat o'zgarishi bilan BIR tranzaksiyada),
keyin bot jarayonidagi ishchi uni yetkazadi va muvaffaqiyatsizlikda qayta urinadi.

`params` da faqat identifikatorlar saqlanadi. Matn, klaviatura va imzolangan havolalar
yuborish vaqtida qaytadan quriladi: imzolangan havola muddati bor va u bazada
saqlanishi kerak emas.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import NOTIFICATION_STATUS_VALUES, NotificationStatus

NOTIFICATION_STATUS_CHECK_NAME = "ck_notification_outbox_status"
NOTIFICATION_DUE_INDEX = "ix_notification_outbox_due"
DEDUP_KEY_MAX = 160
LAST_ERROR_MAX = 500

# Ishchi nomlari (service_heartbeat.name).
OUTBOX_WORKER_HEARTBEAT = "outbox_worker"
RETENTION_HEARTBEAT = "retention"


def notification_status_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in NOTIFICATION_STATUS_VALUES)
    return f"status IN ({values})"


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (
        CheckConstraint(notification_status_check_sql(), name=NOTIFICATION_STATUS_CHECK_NAME),
        # Ishchi har sekundda shu ikki ustun bo'yicha so'raydi.
        Index(NOTIFICATION_DUE_INDEX, "status", "next_attempt_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # Telegram ID lari 2^31 dan katta bo'ladi.
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Yangi kod eski ishchi tushunmaydigan qator yozsa, ishchi uni terminal qilmaydi.
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=NotificationStatus.PENDING.value, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    # NOT NULL va noyob: nullable noyob ustun ikki dialektda ham NULL larni
    # bir-biridan farqli deb hisoblaydi, ya'ni takrorlanishni umuman to'smaydi.
    dedup_key: Mapped[str] = mapped_column(String(DEDUP_KEY_MAX), unique=True, nullable=False)
    # Barcha vaqtlar Python soatidan yoziladi (server_default emas): ijara hisobi
    # bitta soatga tayanishi kerak, SQLite esa timezone ni saqlamaydi.
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ServiceHeartbeat(Base):
    """Fon jarayonlarining oxirgi belgisi.

    Bo'sh navbat "hammasi yetkazildi" degani ham, "ishchi o'lgan" degani ham bo'lishi
    mumkin — shu jadval ikkisini ajratadi.
    """

    __tablename__ = "service_heartbeat"

    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)

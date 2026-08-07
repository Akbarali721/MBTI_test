from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PAYMENT_STATUS_VALUES, PaymentStatus

if TYPE_CHECKING:
    # Modullar bir-biriga havola qiladi: import faqat tipni tekshirishda bajariladi.
    from app.models.personality import PersonalityTestSession

PAYMENT_STATUS_PENDING = PaymentStatus.PENDING.value
PAYMENT_STATUS_RECEIPT_SENT = PaymentStatus.RECEIPT_SENT.value
PAYMENT_STATUS_APPROVED = PaymentStatus.APPROVED.value
PAYMENT_STATUS_REJECTED = PaymentStatus.REJECTED.value

ACTIVE_PAYMENT_STATUSES = frozenset({PAYMENT_STATUS_PENDING, PAYMENT_STATUS_RECEIPT_SENT})

PAYMENT_STATUS_CHECK_NAME = "ck_payment_requests_status"
ACTIVE_PAYMENT_INDEX_NAME = "uq_payment_requests_active_session"


def payment_status_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in PAYMENT_STATUS_VALUES)
    return f"status IN ({values})"


def active_payment_where_sql() -> str:
    values = ", ".join(f"'{value}'" for value in sorted(ACTIVE_PAYMENT_STATUSES))
    return f"status IN ({values})"


class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    __table_args__ = (
        CheckConstraint(payment_status_check_sql(), name=PAYMENT_STATUS_CHECK_NAME),
        # Veb va bot alohida jarayonlar — "bitta faol to'lov" qoidasi baza darajasida
        # majburiy bo'lmasa, bir vaqtda kelgan ikki so'rov ikkita faol qator yaratadi.
        Index(
            ACTIVE_PAYMENT_INDEX_NAME,
            "session_id",
            unique=True,
            sqlite_where=text(active_payment_where_sql()),
            postgresql_where=text(active_payment_where_sql()),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("personality_test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=PAYMENT_STATUS_PENDING, nullable=False, index=True
    )
    receipt_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    receipt_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    receipt_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["PersonalityTestSession"] = relationship(back_populates="payment_requests")

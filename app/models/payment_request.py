from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_RECEIPT_SENT = "receipt_sent"
PAYMENT_STATUS_APPROVED = "approved"
PAYMENT_STATUS_REJECTED = "rejected"
PAYMENT_STATUS_CANCELLED = "cancelled"

ACTIVE_PAYMENT_STATUSES = frozenset({PAYMENT_STATUS_PENDING, PAYMENT_STATUS_RECEIPT_SENT})


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("personality_test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, default=9999, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PAYMENT_STATUS_PENDING, nullable=False, index=True)
    receipt_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    receipt_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    receipt_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["PersonalityTestSession"] = relationship(back_populates="payment_requests")

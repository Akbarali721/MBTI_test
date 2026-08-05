from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.payment_request import (
    ACTIVE_PAYMENT_STATUSES,
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_RECEIPT_SENT,
    PAYMENT_STATUS_REJECTED,
    PaymentRequest,
)
from app.models.personality import PersonalityTestSession


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, payment_id: int) -> PaymentRequest | None:
        return self.db.get(PaymentRequest, payment_id)

    def get_by_id_with_session(self, payment_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.session))
            .where(PaymentRequest.id == payment_id)
        )
        return self.db.scalar(stmt)

    def get_active_for_session(self, session_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .where(
                PaymentRequest.session_id == session_id,
                PaymentRequest.status.in_(ACTIVE_PAYMENT_STATUSES),
            )
            .order_by(desc(PaymentRequest.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_latest_rejected_for_session(self, session_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .where(
                PaymentRequest.session_id == session_id,
                PaymentRequest.status == PAYMENT_STATUS_REJECTED,
            )
            .order_by(desc(PaymentRequest.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_latest_awaiting_receipt_for_user(self, telegram_user_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .where(
                PaymentRequest.telegram_user_id == telegram_user_id,
                PaymentRequest.status.in_(ACTIVE_PAYMENT_STATUSES),
            )
            .order_by(desc(PaymentRequest.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def create_payment(
        self,
        *,
        session_id: int,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
        amount: int,
    ) -> PaymentRequest:
        payment = PaymentRequest(
            session_id=session_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
            amount=amount,
            status=PAYMENT_STATUS_PENDING,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def list_for_admin(
        self,
        *,
        status_filter: str | None = None,
        limit: int = 500,
    ) -> list[PaymentRequest]:
        stmt = (
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.session))
            .order_by(desc(PaymentRequest.created_at))
        )
        if status_filter and status_filter != "all":
            stmt = stmt.where(PaymentRequest.status == status_filter)
        stmt = stmt.limit(limit)
        rows = list(self.db.scalars(stmt).all())
        order = {
            PAYMENT_STATUS_RECEIPT_SENT: 0,
            PAYMENT_STATUS_PENDING: 1,
            PAYMENT_STATUS_APPROVED: 2,
            PAYMENT_STATUS_REJECTED: 3,
        }

        def sort_key(p: PaymentRequest) -> tuple:
            return (order.get(p.status, 99), -(p.created_at.timestamp() if p.created_at else 0))

        rows.sort(key=sort_key)
        return rows

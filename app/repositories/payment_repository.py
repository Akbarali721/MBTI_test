from sqlalchemy import Select, case, desc, func, or_, select
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

# Eski veb to'lovlari egasiz qator uchun 0 sentineli bilan yozilgan, yangilari NULL yozadi.
UNOWNED_TELEGRAM_IDS = (None, 0)

# FOR UPDATE ni qo'llab-quvvatlamaydigan dialektlar (SQLite'da sintaksis xatosi bo'ladi).
_DIALECTS_WITHOUT_ROW_LOCKS = frozenset({"sqlite"})

# Admin ro'yxatida diqqat talab qiladigan to'lovlar tepada turadi.
_ADMIN_STATUS_ORDER = case(
    {
        PAYMENT_STATUS_RECEIPT_SENT: 0,
        PAYMENT_STATUS_PENDING: 1,
        PAYMENT_STATUS_APPROVED: 2,
        PAYMENT_STATUS_REJECTED: 3,
    },
    value=PaymentRequest.status,
    else_=99,
)


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def supports_row_locks(self) -> bool:
        return self.db.get_bind().dialect.name not in _DIALECTS_WITHOUT_ROW_LOCKS

    def get_by_id(self, payment_id: int) -> PaymentRequest | None:
        return self.db.get(PaymentRequest, payment_id)

    def get_by_id_with_session(self, payment_id: int, *, for_update: bool = False) -> PaymentRequest | None:
        lock = for_update and self.supports_row_locks()
        if lock:
            # FOR UPDATE outer join bilan birga ishlamaydi, shuning uchun qator alohida qulflanadi.
            self.db.execute(
                select(PaymentRequest.id).where(PaymentRequest.id == payment_id).with_for_update()
            )
        stmt = (
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.session))
            .where(PaymentRequest.id == payment_id)
        )
        if lock:
            # Qulflangandan keyin identity map'dagi eskirgan qiymatlar qayta o'qiladi.
            stmt = stmt.execution_options(populate_existing=True)
        return self.db.scalar(stmt)

    def get_active_for_session(self, session_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .where(
                PaymentRequest.session_id == session_id,
                PaymentRequest.status.in_(ACTIVE_PAYMENT_STATUSES),
            )
            .order_by(desc(PaymentRequest.created_at), desc(PaymentRequest.id))
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
            .order_by(desc(PaymentRequest.created_at), desc(PaymentRequest.id))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_latest_unowned_awaiting_receipt_for_user(self, telegram_user_id: int) -> PaymentRequest | None:
        """Vebda egasiz boshlangan to'lov: sessiya foydalanuvchiga bog'langan, to'lov qatori esa yo'q."""
        stmt = (
            select(PaymentRequest)
            .join(PersonalityTestSession, PersonalityTestSession.id == PaymentRequest.session_id)
            .where(
                PersonalityTestSession.telegram_user_id == telegram_user_id,
                or_(
                    PaymentRequest.telegram_user_id.is_(None),
                    PaymentRequest.telegram_user_id == 0,
                ),
                PaymentRequest.status.in_(ACTIVE_PAYMENT_STATUSES),
            )
            .order_by(desc(PaymentRequest.created_at), desc(PaymentRequest.id))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_latest_rejected_for_user(self, telegram_user_id: int) -> PaymentRequest | None:
        stmt = (
            select(PaymentRequest)
            .where(
                PaymentRequest.telegram_user_id == telegram_user_id,
                PaymentRequest.status == PAYMENT_STATUS_REJECTED,
            )
            .order_by(desc(PaymentRequest.created_at), desc(PaymentRequest.id))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def create_payment(
        self,
        *,
        session_id: int,
        telegram_user_id: int | None,
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
        # Bot handlerlari o'z sessiyasini o'zi ochadi va commit qilmaydi, shuning uchun
        # to'lov yaratilishi shu yerda yakunlanadi (premium_payment_service bilan bir xil shartnoma).
        self.db.commit()
        self.db.refresh(payment)
        return payment

    @staticmethod
    def _apply_admin_filter(stmt: Select, status_filter: str | None) -> Select:
        if status_filter and status_filter != "all":
            return stmt.where(PaymentRequest.status == status_filter)
        return stmt

    def count_for_admin(self, *, status_filter: str | None = None) -> int:
        stmt = self._apply_admin_filter(select(func.count()).select_from(PaymentRequest), status_filter)
        return int(self.db.scalar(stmt) or 0)

    def list_for_admin(
        self,
        *,
        status_filter: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[PaymentRequest]:
        """Saralash SQL'da: LIMIT butun to'plam tartiblangandan keyin qo'llanadi."""
        stmt = (
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.session))
            .order_by(_ADMIN_STATUS_ORDER, desc(PaymentRequest.created_at), desc(PaymentRequest.id))
        )
        stmt = self._apply_admin_filter(stmt, status_filter).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

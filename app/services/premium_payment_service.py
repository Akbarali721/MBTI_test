from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.models.payment_request import (
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_RECEIPT_SENT,
    PAYMENT_STATUS_REJECTED,
    PaymentRequest,
)
from app.models.personality import PersonalityTestSession
from app.personality.payment_code import find_sessions_by_payment_code
from app.repositories.payment_repository import UNOWNED_TELEGRAM_IDS, PaymentRepository
from app.repositories.personality_repository import PersonalityRepository
from app.services.admin_service import admin_chat_ids
from app.services.notification_outbox import (
    ADMIN_RECEIPT,
    PREMIUM_PDF,
    USER_APPROVED,
    USER_REJECTED,
    dedup_key,
    enqueue,
    event_stamp,
)

RESULT_ACCESS_QUERY_KEY = "access"
MIN_SESSION_TOKEN_LENGTH = 24


@dataclass(frozen=True)
class PremiumStartOutcome:
    code: str
    session: PersonalityTestSession | None = None
    payment: PaymentRequest | None = None


@dataclass(frozen=True)
class PaymentCodeOutcome:
    code: str
    session: PersonalityTestSession | None = None
    payment: PaymentRequest | None = None
    matches: int = 0


@dataclass(frozen=True)
class ReceiptOutcome:
    code: str
    payment: PaymentRequest | None = None


@dataclass(frozen=True)
class ModerationOutcome:
    code: str
    payment: PaymentRequest | None = None
    session: PersonalityTestSession | None = None


def parse_premium_session_token(start_payload: str) -> str | None:
    prefix = "premium_"
    if not start_payload or not start_payload.startswith(prefix):
        return None
    token = start_payload[len(prefix) :].strip()
    if not token or len(token) > 64 or not token.isalnum():
        return None
    return token


def result_url_for_token(token: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/personality/result/{token}"


def signed_result_url_for_token(token: str) -> str:
    """Telegramdan kelgan foydalanuvchida veb cookie bo'lmaydi, shuning uchun imzolangan havola."""
    url = result_url_for_token(token)
    try:
        from app.personality.session_binding import make_result_access_token
    except ImportError:
        # Imzolash yordamchisi hali qo'shilmagan bo'lsa, oddiy havola qaytadi.
        return url
    access = make_result_access_token(token)
    if not access:
        return url
    return f"{url}?{RESULT_ACCESS_QUERY_KEY}={quote(access, safe='')}"


def format_price_uzs(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def support_bot_public_url() -> str | None:
    username = (settings.payment_support_bot_username or "").strip().lstrip("@")
    if not username:
        return None
    return f"https://t.me/{username}"


def premium_bot_username() -> str:
    """Bot that actually runs the receipt handlers, falling back to the advertised one."""
    for candidate in (settings.bot_username, settings.payment_support_bot_username):
        cleaned = (candidate or "").strip().lstrip("@")
        if cleaned:
            return cleaned
    return ""


def premium_deeplink_url(token: str) -> str | None:
    """Deep link that binds the payer's Telegram account to this test session."""
    username = premium_bot_username()
    if not username:
        return None
    return f"https://t.me/{username}?start=premium_{token}"


def enqueue_premium_granted(
    db: Session,
    *,
    session: PersonalityTestSession,
    chat_id: int | None,
) -> None:
    """Premium ochilganda mijozga xabar va PDF hisobotni navbatga qo'yadi.

    Telegram ID bo'lmasa (masalan admin qo'lda ochgan, mijoz esa botga kirmagan)
    yuboradigan manzil yo'q — bu holat admin panelida ko'rinadi.

    dedup_key HODISADAN, ya'ni `session.premium_approved_at` dan olinadi va to'lov
    qatoridan emas. Sababi: "premium ochildi" sessiya uchun BIR MARTALIK hodisa.
    Ikki ishlab chiqaruvchi (admin qo'lda ochishi va to'lovni tasdiqlashi) turli
    ustundan vaqt olganda kalitlar farq qilib, mijoz ikkita xabar va ikkita PDF
    olardi — yuborish paytidagi tekshiruv ham buni to'sa olmaydi, chunki ikkalasida
    ham sessiya haqiqatan premium.
    """
    if not chat_id:
        return
    stamp = event_stamp(session.premium_approved_at)
    params = {"session_id": session.id}
    enqueue(
        db,
        kind=USER_APPROVED,
        chat_id=chat_id,
        params=params,
        key=dedup_key(USER_APPROVED, chat_id, session.id, stamp),
    )
    enqueue(
        db,
        kind=PREMIUM_PDF,
        chat_id=chat_id,
        params=params,
        key=dedup_key(PREMIUM_PDF, chat_id, session.id, stamp),
    )


class PremiumPaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payments = PaymentRepository(db)
        self.sessions = PersonalityRepository(db)

    def start_premium_from_deeplink(
        self,
        *,
        session_token: str,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
    ) -> PremiumStartOutcome:
        session = self.sessions.get_session_by_token(session_token)
        if not session:
            return PremiumStartOutcome(code="invalid_token")

        if session.status != PersonalitySessionStatus.COMPLETED:
            return PremiumStartOutcome(code="incomplete", session=session)

        if session.is_premium:
            return PremiumStartOutcome(code="already_premium", session=session)

        active = self.payments.get_active_for_session(session.id)
        if self._is_owned_by_other(session, telegram_user_id, active):
            return PremiumStartOutcome(code="owned_by_other", session=session, payment=active)

        payment = self._bind_session_and_payment(
            session=session,
            active=active,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
        )
        code = "existing_active" if active is not None else "created"
        return PremiumStartOutcome(code=code, session=session, payment=payment)

    def claim_by_payment_code(
        self,
        *,
        payment_code: str,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
    ) -> PaymentCodeOutcome:
        """Test kodi bo'yicha sessiyani topib, uni chek yuboradigan Telegram akkauntga bog'laydi."""
        sessions = find_sessions_by_payment_code(self.db, payment_code)
        if not sessions:
            by_token = self._session_by_full_token(payment_code)
            if by_token is None:
                return PaymentCodeOutcome(code="not_found")
            sessions = [by_token]

        if len(sessions) > 1:
            return PaymentCodeOutcome(code="ambiguous", matches=len(sessions))

        session = sessions[0]
        if session.status != PersonalitySessionStatus.COMPLETED:
            return PaymentCodeOutcome(code="incomplete", session=session)
        if session.is_premium:
            return PaymentCodeOutcome(code="already_premium", session=session)

        active = self.payments.get_active_for_session(session.id)
        if self._is_owned_by_other(session, telegram_user_id, active):
            return PaymentCodeOutcome(code="owned_by_other", session=session, payment=active)

        payment = self._bind_session_and_payment(
            session=session,
            active=active,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
        )
        return PaymentCodeOutcome(code="claimed", session=session, payment=payment)

    def attach_receipt(
        self,
        *,
        telegram_user_id: int,
        receipt_file_id: str,
        receipt_type: str,
        payment_id: int | None = None,
    ) -> ReceiptOutcome:
        target = self._resolve_receipt_target(telegram_user_id, payment_id)
        if target is None:
            return ReceiptOutcome(code="no_active_payment")

        payment = self.payments.get_by_id_with_session(target.id, for_update=True)
        if payment is None:
            return ReceiptOutcome(code="no_active_payment")

        if payment.status == PAYMENT_STATUS_APPROVED:
            return ReceiptOutcome(code="already_approved", payment=payment)

        if payment.status == PAYMENT_STATUS_REJECTED:
            # Rad etilgan urinish dalil sifatida tarixda qoladi, yangi urinish yangi qatorga yoziladi.
            payment = self.payments.create_payment(
                session_id=payment.session_id,
                telegram_user_id=telegram_user_id,
                telegram_username=payment.telegram_username,
                telegram_first_name=payment.telegram_first_name,
                amount=payment.amount or settings.premium_price,
            )
        elif payment.status not in (PAYMENT_STATUS_PENDING, PAYMENT_STATUS_RECEIPT_SENT):
            return ReceiptOutcome(code="not_acceptable", payment=payment)

        if payment.telegram_user_id in UNOWNED_TELEGRAM_IDS:
            # Vebda egasiz boshlangan to'lov shu yerda o'z egasini topadi.
            payment.telegram_user_id = telegram_user_id

        now = datetime.now(timezone.utc)
        payment.receipt_file_id = receipt_file_id
        payment.receipt_type = receipt_type
        payment.status = PAYMENT_STATUS_RECEIPT_SENT
        payment.receipt_sent_at = now
        payment.rejected_at = None
        # Bildirishnoma AYNAN shu tranzaksiyada yoziladi: chek saqlanib, adminga
        # xabar navbatga tushmay qolgan holat bo'lmasligi kerak.
        self.db.flush()
        self._enqueue_admin_receipt(payment)
        self.db.commit()
        self.db.refresh(payment)
        return ReceiptOutcome(code="saved", payment=payment)

    def approve_payment(self, payment_id: int, *, approved_by: str) -> ModerationOutcome:
        payment = self.payments.get_by_id_with_session(payment_id, for_update=True)
        if not payment:
            return ModerationOutcome(code="not_found")

        session = payment.session
        if session is None:
            return ModerationOutcome(code="not_found", payment=payment)

        if payment.status == PAYMENT_STATUS_APPROVED and session.is_premium:
            return ModerationOutcome(code="already_approved", payment=payment, session=session)

        now = datetime.now(timezone.utc)
        payment.status = PAYMENT_STATUS_APPROVED
        payment.approved_at = payment.approved_at or now
        payment.approved_by = approved_by
        payment.rejected_at = None

        session.is_premium = True
        session.premium_requested = True
        session.premium_requested_at = session.premium_requested_at or now
        session.premium_approved_at = session.premium_approved_at or now

        self.db.flush()
        enqueue_premium_granted(self.db, session=session, chat_id=payment.telegram_user_id)
        self.db.commit()
        self.db.refresh(payment)
        self.db.refresh(session)
        return ModerationOutcome(code="approved", payment=payment, session=session)

    def reject_payment(self, payment_id: int, *, approved_by: str) -> ModerationOutcome:
        payment = self.payments.get_by_id_with_session(payment_id, for_update=True)
        if not payment:
            return ModerationOutcome(code="not_found")

        session = payment.session
        if session is None:
            return ModerationOutcome(code="not_found", payment=payment)

        if payment.status == PAYMENT_STATUS_APPROVED:
            return ModerationOutcome(code="already_approved", payment=payment, session=session)
        if session.is_premium:
            # Aks holda status=rejected bo'lgan to'lov ochiq premium bilan yonma-yon qoladi.
            return ModerationOutcome(code="already_premium", payment=payment, session=session)

        now = datetime.now(timezone.utc)
        payment.status = PAYMENT_STATUS_REJECTED
        payment.rejected_at = now
        payment.approved_by = approved_by

        self.db.flush()
        if payment.telegram_user_id:
            enqueue(
                self.db,
                kind=USER_REJECTED,
                chat_id=payment.telegram_user_id,
                params={"payment_id": payment.id, "session_id": session.id},
                key=dedup_key(
                    USER_REJECTED, payment.telegram_user_id, payment.id, event_stamp(payment.rejected_at)
                ),
            )
        self.db.commit()
        self.db.refresh(payment)
        self.db.refresh(session)
        return ModerationOutcome(code="rejected", payment=payment, session=session)

    def get_result_payment_status(self, session: PersonalityTestSession) -> str:
        """unpaid / awaiting_receipt / reviewing / approved.

        Holatlar ajratilgan: chek hali yuborilmaganda natija sahifasi "chekingiz
        administratorga yuborildi" deb yolg'on xabar bermasligi kerak.
        """
        if session.is_premium:
            return "approved"
        active = self.payments.get_active_for_session(session.id)
        if active is None:
            return "unpaid"
        if active.status == PAYMENT_STATUS_RECEIPT_SENT:
            return "reviewing"
        if active.status == PAYMENT_STATUS_PENDING:
            return "awaiting_receipt"
        return "unpaid"

    def begin_web_manual_payment(self, session_token: str) -> PaymentRequest | None:
        session = self.sessions.get_session_by_token(session_token)
        if not session:
            return None
        if session.status != PersonalitySessionStatus.COMPLETED or session.is_premium:
            return None

        now = datetime.now(timezone.utc)
        session.premium_requested = True
        session.premium_requested_at = session.premium_requested_at or now

        active = self.payments.get_active_for_session(session.id)
        if active:
            self.db.commit()
            self.db.refresh(active)
            return active

        # Egasi hali noma'lum: sentinel 0 emas, NULL yoziladi — foydalanuvchi test kodini
        # botga yuborganda qator unga biriktiriladi.
        payment = self.payments.create_payment(
            session_id=session.id,
            telegram_user_id=session.telegram_user_id,
            telegram_username=session.telegram_username,
            telegram_first_name=session.telegram_first_name,
            amount=settings.premium_price,
        )
        self.db.refresh(session)
        return payment

    def _bind_session_and_payment(
        self,
        *,
        session: PersonalityTestSession,
        active: PaymentRequest | None,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
    ) -> PaymentRequest:
        now = datetime.now(timezone.utc)
        session.telegram_user_id = telegram_user_id
        session.telegram_username = telegram_username
        session.telegram_first_name = telegram_first_name
        session.premium_requested = True
        session.premium_requested_at = session.premium_requested_at or now

        if active is not None:
            self._sync_payment_user(active, telegram_user_id, telegram_username, telegram_first_name)
            self.db.commit()
            self.db.refresh(active)
            self.db.refresh(session)
            return active

        payment = self.payments.create_payment(
            session_id=session.id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
            amount=settings.premium_price,
        )
        self.db.refresh(session)
        return payment

    def _enqueue_admin_receipt(self, payment: PaymentRequest) -> None:
        """Chek haqida BARCHA moderatorlarga xabar (bittasi javob bermay qolmasin)."""
        stamp = event_stamp(payment.receipt_sent_at)
        for chat_id in admin_chat_ids(self.db):
            enqueue(
                self.db,
                kind=ADMIN_RECEIPT,
                chat_id=chat_id,
                params={"payment_id": payment.id, "session_id": payment.session_id},
                key=dedup_key(ADMIN_RECEIPT, chat_id, payment.id, stamp),
            )

    def _session_by_full_token(self, value: str) -> PersonalityTestSession | None:
        cleaned = value.strip().lower()
        if len(cleaned) < MIN_SESSION_TOKEN_LENGTH or not cleaned.isalnum():
            return None
        return self.sessions.get_session_by_token(cleaned)

    def _resolve_receipt_target(self, telegram_user_id: int, payment_id: int | None) -> PaymentRequest | None:
        if payment_id is not None:
            candidate = self.payments.get_by_id(payment_id)
            if candidate is not None and self._may_use(candidate, telegram_user_id):
                return candidate
        owned = self.payments.get_latest_awaiting_receipt_for_user(telegram_user_id)
        if owned is not None:
            return owned
        unowned = self.payments.get_latest_unowned_awaiting_receipt_for_user(telegram_user_id)
        if unowned is not None:
            return unowned
        return self.payments.get_latest_rejected_for_user(telegram_user_id)

    @staticmethod
    def _may_use(payment: PaymentRequest, telegram_user_id: int) -> bool:
        if payment.telegram_user_id == telegram_user_id:
            return True
        if payment.telegram_user_id not in UNOWNED_TELEGRAM_IDS:
            return False
        session = payment.session
        return session is not None and session.telegram_user_id == telegram_user_id

    @staticmethod
    def _is_owned_by_other(
        session: PersonalityTestSession,
        telegram_user_id: int,
        active: PaymentRequest | None,
    ) -> bool:
        """Havola tarqalsa begona odam faol to'lovni o'ziga o'tkazib olmasligi uchun."""
        owner = session.telegram_user_id
        if owner in UNOWNED_TELEGRAM_IDS or owner == telegram_user_id:
            return False
        return active is not None

    @staticmethod
    def _sync_payment_user(
        payment: PaymentRequest,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
    ) -> None:
        payment.telegram_user_id = telegram_user_id
        payment.telegram_username = telegram_username
        payment.telegram_first_name = telegram_first_name

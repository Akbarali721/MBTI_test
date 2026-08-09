"""Referal: do'st taklif qilib bepul premium olish.

Qoida: taklif havolasi orqali kelgan N ta odam testni OXIRIGACHA tugatsa, taklif
qilgan odamga premium bir necha kunga ochiladi (sozlamada: 3 ta odam -> 3 kun).

Havola sifatida sessiyaning mavjud `share_code` i ishlatiladi. Alohida "referal kodi"
qo'shilmadi: shunda odam natijasini ulashsa, o'sha havolaning O'ZI mukofot keltiradi
— ya'ni allaqachon tarqatilgan havolalar ham ishlay boshlaydi. Kod tokendan mustaqil,
demak uni tarqatish natijaga kirish huquqini bermaydi.

SUISTE'MOLGA QARSHI. Bu funksiya tabiatan suiiste'mol qilinadi, shuning uchun
qoidalar bir joyda va aniq:

* Biriktirish faqat sessiya YARATILGANDA. Keyin o'zgartirilsa, havola tarqatgan odam
  begona tugallangan testni o'z hisobiga o'tkazib olardi.
* Brauzerda ALLAQACHON tugatilgan test bo'lsa, biriktirish bo'lmaydi. Bu ikkita
  eng arzon yo'lni yopadi: o'z havolangni o'zing bosish va bitta brauzerda testni
  qayta-qayta topshirib hisob to'plash.
* Faqat TUGATILGAN sessiyalar sanaladi va sanoq har safar bazadan qaytadan
  o'qiladi (hisoblagich saqlanmaydi), ya'ni bir sessiya ikki marta sanalmaydi.
* Mukofot `referral_milestones_granted` bo'yicha compare-and-swap bilan beriladi:
  ikki do'st bir lahzada tugatsa ham u ikki marta berilmaydi.
* Yig'ilgan bepul muddat yuqoridan cheklangan (REFERRAL_MAX_REWARD_DAYS).

Yopilmagan yo'l: har safar toza brauzer profilida (yoki inkognitoda) 24 ta savolga
javob berish. Buni to'sish uchun IP yoki qurilma izini saqlash kerak bo'lardi —
loyiha ataylab ularni yig'maydi. Shuning uchun mukofot cheklangan va admin panelida
referal ko'rsatkichlari ko'rinib turadi.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.services.premium_access import premium_expires_at
from app.timeutils import as_utc, utcnow

logger = logging.getLogger(__name__)

REFERRAL_QUERY_KEY = "ref"
# share_code — secrets.token_urlsafe(8), ya'ni [A-Za-z0-9_-]. Uzunlik ustun bo'yi
# bilan cheklanadi: uzun qiymat baribir topilmaydi, lekin so'rovni bekorga qiladi.
MAX_CODE_LENGTH = 24
_CODE_RE = re.compile(rf"^[A-Za-z0-9_-]{{1,{MAX_CODE_LENGTH}}}$")


@dataclass(frozen=True)
class ReferralProgress:
    """Natija sahifasidagi "2/3 do'st tugatdi" bloki uchun."""

    code: str
    invited: int
    completed: int
    required: int
    milestones_granted: int
    premium_until: datetime | None

    @property
    def toward_next(self) -> int:
        """Navbatdagi mukofotga qancha qolgani (0..required-1)."""
        return self.completed % self.required if self.required else 0

    @property
    def remaining(self) -> int:
        return max(0, self.required - self.toward_next)

    @property
    def percent(self) -> int:
        return min(100, round(self.toward_next / self.required * 100)) if self.required else 0


@dataclass(frozen=True)
class RewardOutcome:
    """Mukofot berildi. `chat_id` bo'lsa foydalanuvchiga xabar yuboriladi."""

    referrer_id: int
    milestones: int
    days: int
    premium_until: datetime
    chat_id: int | None


def normalize_code(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = raw.strip()
    if not _CODE_RE.match(cleaned):
        return None
    return cleaned


def referral_url(code: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/personality?{REFERRAL_QUERY_KEY}={code}"


def find_referrer(db: Session, code: str) -> PersonalityTestSession | None:
    """Kod bo'yicha taklif qiluvchi sessiya — faqat testni tugatgani."""
    normalized = normalize_code(code)
    if not normalized:
        return None
    stmt = select(PersonalityTestSession).where(
        PersonalityTestSession.share_code == normalized,
        PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
    )
    return db.scalar(stmt)


def may_attribute(session: PersonalityTestSession) -> bool:
    """Sessiya hali BOSHLANMAGAN bo'lsagina biriktirish mumkin.

    Bu invariant butun suiiste'mol himoyasini ushlab turadi: allaqachon javob
    berilgan (yoki tugatilgan) testni keyin kimningdir hisobiga o'tkazib bo'lmaydi.
    Ayni paytda kecha saytga kirib, bugun do'stining havolasi bilan qaytgan odam
    hisobga olinaveradi — uning sessiyasi hali VISITED.
    """
    return (
        session.referred_by_session_id is None
        and session.status == PersonalitySessionStatus.VISITED
        and not session.answered_questions
    )


def attribute_session(
    db: Session,
    *,
    session: PersonalityTestSession,
    code: str | None,
    browser_has_completed_test: bool,
) -> bool:
    """Sessiyani taklif qiluvchiga biriktiradi. True — biriktirildi.

    `browser_has_completed_test` — shu brauzerda avval tugatilgan test bormi.
    Bor bo'lsa bu "yangi odam" emas va hisobga olinmaydi.
    """
    if not settings.referral_enabled or not code:
        return False
    if not may_attribute(session):
        return False
    if browser_has_completed_test:
        return False
    referrer = find_referrer(db, code)
    if referrer is None or referrer.id == session.id:
        return False
    session.referred_by_session_id = referrer.id
    db.flush()
    return True


def completed_referral_count(db: Session, referrer_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(PersonalityTestSession)
        .where(
            PersonalityTestSession.referred_by_session_id == referrer_id,
            PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
        )
    )
    return int(db.scalar(stmt) or 0)


def invited_count(db: Session, referrer_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(PersonalityTestSession)
        .where(PersonalityTestSession.referred_by_session_id == referrer_id)
    )
    return int(db.scalar(stmt) or 0)


def progress(db: Session, session: PersonalityTestSession, *, code: str) -> ReferralProgress:
    return ReferralProgress(
        code=code,
        invited=invited_count(db, session.id),
        completed=completed_referral_count(db, session.id),
        required=max(1, settings.referral_required_completions),
        milestones_granted=session.referral_milestones_granted or 0,
        premium_until=premium_expires_at(session),
    )


def _next_expiry(current: datetime | None, *, days: int, now: datetime) -> datetime:
    """Mukofot muddatni UZAYTIRADI, boshidan boshlamaydi.

    Aks holda ikkinchi mukofot birinchisidan qolgan kunlarni o'chirib yuborardi.
    Yig'indi yuqoridan cheklanadi: mukofot takrorlanadigan bo'lgani uchun cheklovsiz
    qoldirilsa, bepul muddat cheksiz o'sib ketardi.
    """
    base = current if current is not None and current > now else now
    ceiling = now + timedelta(days=settings.referral_max_reward_days)
    return min(base + timedelta(days=days), ceiling)


def reward_referrer_if_earned(
    db: Session,
    completed_session: PersonalityTestSession,
    *,
    now: datetime | None = None,
) -> RewardOutcome | None:
    """Test tugagach chaqiriladi: taklif qilgan odamga mukofot yetdimi?

    Chaqiruvchining tranzaksiyasida ishlaydi va COMMIT QILMAYDI — mukofot testni
    tugatish bilan bir tranzaksiyada yozilishi kerak.
    """
    if not settings.referral_enabled:
        return None
    referrer_id = completed_session.referred_by_session_id
    if not referrer_id:
        return None
    if completed_session.status != PersonalitySessionStatus.COMPLETED:
        return None

    required = max(1, settings.referral_required_completions)
    earned = completed_referral_count(db, referrer_id) // required
    if earned < 1:
        return None

    referrer = db.get(PersonalityTestSession, referrer_id)
    if referrer is None or (referrer.referral_milestones_granted or 0) >= earned:
        return None

    moment = as_utc(now) or utcnow()
    days = settings.referral_reward_days * (earned - (referrer.referral_milestones_granted or 0))
    expires = _next_expiry(premium_expires_at(referrer), days=days, now=moment)

    # Compare-and-swap: `SELECT FOR UPDATE` SQLite'da yo'q, shuning uchun shart
    # UPDATE ning O'ZIDA. Ikkinchi bir vaqtdagi chaqiruv 0 qator yangilaydi.
    result = db.execute(
        update(PersonalityTestSession)
        .where(
            PersonalityTestSession.id == referrer_id,
            PersonalityTestSession.referral_milestones_granted < earned,
        )
        .values(referral_milestones_granted=earned, premium_until=expires)
    )
    if getattr(result, "rowcount", 0) != 1:
        logger.info("Referal mukofoti allaqachon berilgan: sessiya #%s", referrer_id)
        return None

    db.expire(referrer)
    logger.info(
        "Referal mukofoti: sessiya #%s, %s kun, %s gacha",
        referrer_id,
        days,
        expires.isoformat(),
    )
    return RewardOutcome(
        referrer_id=referrer_id,
        milestones=earned,
        days=days,
        premium_until=expires,
        chat_id=referrer.telegram_user_id,
    )

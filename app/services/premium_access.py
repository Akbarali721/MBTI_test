"""Premium kirish huquqi — ikki manbadan: pul to'langan yoki referal mukofoti.

Bu modul ATAYLAB juda kichik va hech narsani import qilmaydi (modeldan tashqari):
uni veb, bot, PDF va analitika birdek chaqiradi.

Uchta tushuncha aralashib ketmasligi kerak:

* `is_premium` — PUL TO'LANGAN, muddatsiz. Voronka, A/B konversiyasi va "sotib olish"
  oqimidagi barcha tekshiruvlar SHUNGA qaraydi. Bepul mukofot bu ustunga tegmaydi,
  aks holda hisobotlarda u sotuv bo'lib ko'rinardi.
* `premium_until` — mukofot bergan vaqtli kirish.
* `has_premium_access` — foydalanuvchi hozir premium bo'limlarni KO'RA OLADIMI.
  Faqat kontentni ko'rsatish uchun ishlatiladi.

PDF ataylab shu ro'yxatga kirmaydi: yuklab olingan fayl 3 kundan keyin ham qo'lda
qoladi, ya'ni vaqtli mukofot orqali berilsa muddat degan narsa qolmasdi.
"""

from __future__ import annotations

from datetime import datetime

from app.models.personality import PersonalityTestSession
from app.timeutils import as_utc, utcnow

SECONDS_IN_DAY = 24 * 3600


def premium_expires_at(session: PersonalityTestSession) -> datetime | None:
    """Vaqtli premium tugash lahzasi (UTC, aware). Muddati o'tgan bo'lsa ham qaytadi."""
    return as_utc(session.premium_until)


def has_trial_premium(session: PersonalityTestSession, *, now: datetime | None = None) -> bool:
    expires = premium_expires_at(session)
    return expires is not None and expires > (as_utc(now) or utcnow())


def has_premium_access(session: PersonalityTestSession, *, now: datetime | None = None) -> bool:
    return bool(session.is_premium) or has_trial_premium(session, now=now)


def trial_seconds_left(session: PersonalityTestSession, *, now: datetime | None = None) -> int:
    expires = premium_expires_at(session)
    if expires is None:
        return 0
    delta = (expires - (as_utc(now) or utcnow())).total_seconds()
    return max(0, int(delta))


def trial_days_left(session: PersonalityTestSession, *, now: datetime | None = None) -> int:
    """Foydalanuvchiga ko'rsatiladigan kun soni — yuqoriga yaxlitlanadi.

    Pastga yaxlitlash 20 soat qolganda "0 kun qoldi" deb yozib, hali ochiq
    premiumni tugagandek ko'rsatardi.
    """
    seconds = trial_seconds_left(session, now=now)
    if seconds <= 0:
        return 0
    return -(-seconds // SECONDS_IN_DAY)

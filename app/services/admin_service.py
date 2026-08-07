"""Admin hisoblari: autentifikatsiya, rollar va audit yozuvi.

Ikkita manba bor va ular ATAYLAB shu tartibda tekshiriladi:

1. `admin_users` jadvali. Login uchun qator topilsa — u hokim. Qator nofaol bo'lsa
   kirish rad etiladi va `.env` ga "tushib ketish" yo'q, aks holda hisobni
   o'chirib qo'yish hech narsani anglatmasdi.
2. `.env` dagi ADMIN_USERNAME/ADMIN_PASSWORD_HASH — zaxira ("break-glass") hisob.
   U uchun bazada qator YARATILMAYDI: shunda ko'p jarayonli bootstrap poygasi ham,
   "parolni .env da almashtirdim, lekin eski parol ishlayapti" hayrati ham bo'lmaydi.
   ADMIN_ENV_LOGIN_ENABLED=false bilan butunlay o'chiriladi.
"""

from __future__ import annotations

import hmac
import logging
import re
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.authz import ACTOR_TELEGRAM, ACTOR_WEB, AdminIdentity
from app.config import admin_credential_problems, hash_password, settings, verify_password
from app.models.admin import USERNAME_PATTERN, AdminUser
from app.models.enums import AdminRole
from app.repositories.admin_repository import AdminRepository, normalize_username

logger = logging.getLogger(__name__)

_USERNAME_RE = re.compile(USERNAME_PATTERN)
_dummy_hash: str | None = None


def _fallback_hash() -> str:
    """Hisob topilmaganda ham verify bir xil vaqt olishi uchun soxta hash."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password(secrets.token_urlsafe(32))
    return _dummy_hash


@dataclass(frozen=True)
class UserChangeResult:
    ok: bool
    error: str | None = None
    user: AdminUser | None = None


def identity_from_user(user: AdminUser, *, actor_type: str = ACTOR_WEB) -> AdminIdentity:
    return AdminIdentity(
        username=user.username,
        role=user.admin_role,
        user_id=user.id,
        telegram_user_id=user.telegram_user_id,
        actor_type=actor_type,
    )


def env_admin_username() -> str:
    return normalize_username(settings.admin_username)


def env_identity() -> AdminIdentity:
    return AdminIdentity(username=env_admin_username(), role=AdminRole.OWNER, actor_type=ACTOR_WEB)


def authenticate(db: Session, username: str, password: str) -> AdminIdentity | None:
    """Login/parolni tekshiradi.

    `verify_password` HAR yo'lda ROSA BIR MARTA chaqiriladi — aks holda javob vaqti
    "bunday login bor" va "yo'q" holatlarini ajratib berardi.
    """
    cleaned = normalize_username(username)
    repo = AdminRepository(db)
    row = repo.get_by_username(cleaned)

    candidate: str | None = None
    identity: AdminIdentity | None = None

    if row is not None:
        if row.is_active:
            candidate = row.password_hash
            identity = identity_from_user(row)
    elif settings.admin_env_login_enabled and cleaned:
        expected = env_admin_username()
        if expected and hmac.compare_digest(cleaned.encode("utf-8"), expected.encode("utf-8")):
            candidate = settings.admin_password_hash or None
            identity = env_identity()

    ok = verify_password(password, candidate or _fallback_hash())
    if not ok or candidate is None or identity is None:
        return None

    if row is not None:
        repo.touch_login(row)
    return identity


def resolve_web_identity(db: Session, *, user_id: int | None, username: str) -> AdminIdentity | None:
    """Sessiya cookie'sidan shaxsni QAYTA tiklaydi.

    Rol cookie'da saqlanmaydi va har so'rovda bazadan o'qiladi: aks holda rolni
    pasaytirish yoki hisobni o'chirish ochiq sessiyaga umuman ta'sir qilmasdi
    (Starlette cookie'ni har javobda qayta imzolaydi, ya'ni muddat "siljib" boradi).
    """
    repo = AdminRepository(db)
    if user_id is not None:
        row = repo.get_by_id(user_id)
        if row is None or not row.is_active:
            return None
        return identity_from_user(row)

    if not settings.admin_env_login_enabled:
        return None
    expected = env_admin_username()
    cleaned = normalize_username(username)
    if not expected or cleaned != expected:
        return None
    # `authenticate` bilan bir xil ustunlik: shu nom bilan bazada qator bo'lsa,
    # u hokim. Aks holda o'sha qatorni o'chirish yangi kirishni to'sardi-yu,
    # ochiq turgan `.env` sessiyasi egasi huquqida qolaverardi.
    shadow = repo.get_by_username(cleaned)
    if shadow is not None:
        return identity_from_user(shadow) if shadow.is_active else None
    return env_identity()


def telegram_identity(db: Session, telegram_user_id: int) -> AdminIdentity | None:
    """Bot uchun: avval `.env` ro'yxati (I/O siz), keyin baza."""
    if telegram_user_id in settings.admin_telegram_id_set:
        return AdminIdentity(
            username=str(telegram_user_id),
            role=AdminRole.OWNER,
            telegram_user_id=telegram_user_id,
            actor_type=ACTOR_TELEGRAM,
        )
    row = AdminRepository(db).get_by_telegram_id(telegram_user_id)
    if row is None or not row.is_active:
        return None
    return identity_from_user(row, actor_type=ACTOR_TELEGRAM)


def admin_chat_ids(db: Session) -> list[int]:
    """Chek kelganda xabar yuboriladigan barcha Telegram ID lar."""
    ids = set(settings.admin_telegram_id_set)
    for telegram_id, row in AdminRepository(db).active_telegram_admins().items():
        # Faqat moderatsiya qila oladigan rollarga xabar yuborish mantiqan to'g'ri.
        if row.admin_role in (AdminRole.OWNER, AdminRole.MODERATOR):
            ids.add(telegram_id)
    return sorted(ids)


# --- Hisoblarni boshqarish ---


def _username_problem(username: str) -> str | None:
    if not _USERNAME_RE.match(username):
        return "Login 3-32 belgidan iborat bo'lib, faqat a-z, 0-9, nuqta, chiziqcha va _ dan tuzilsin"
    return None


def create_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: AdminRole,
    telegram_user_id: int | None = None,
) -> UserChangeResult:
    cleaned = normalize_username(username)
    problem = _username_problem(cleaned)
    if problem:
        return UserChangeResult(ok=False, error=problem)

    # Bazadagi hisob ham `.env` hisobi bilan bir xil parol siyosatidan o'tadi.
    problems = admin_credential_problems(cleaned, password, debug=settings.debug)
    if problems:
        return UserChangeResult(ok=False, error="; ".join(problems))

    if settings.admin_env_login_enabled and cleaned == env_admin_username():
        # Bu nom `.env` dagi zaxira hisobga tegishli; bazada ham shu nomda qator
        # bo'lsa ikkita "kim hokim" holati chalkashib ketardi.
        return UserChangeResult(ok=False, error="Bu login `.env` dagi zaxira hisobga tegishli")

    repo = AdminRepository(db)
    if repo.get_by_username(cleaned) is not None:
        return UserChangeResult(ok=False, error="Bunday login allaqachon mavjud")
    if telegram_user_id is not None and repo.get_by_telegram_id(telegram_user_id) is not None:
        return UserChangeResult(ok=False, error="Bu Telegram ID boshqa hisobga biriktirilgan")

    user = repo.create_user(
        username=cleaned,
        password_hash=hash_password(password),
        role=role,
        telegram_user_id=telegram_user_id,
    )
    return UserChangeResult(ok=True, user=user)


def set_password(db: Session, user: AdminUser, password: str) -> UserChangeResult:
    problems = admin_credential_problems(user.username, password, debug=settings.debug)
    if problems:
        return UserChangeResult(ok=False, error="; ".join(problems))
    user.password_hash = hash_password(password)
    db.flush()
    return UserChangeResult(ok=True, user=user)


LAST_OWNER_ERROR = "Oxirgi faol egani o'zgartirib bo'lmaydi"


def set_role(db: Session, user: AdminUser, role: AdminRole, *, actor: AdminIdentity) -> UserChangeResult:
    if user.id == actor.user_id and role != AdminRole.OWNER:
        return UserChangeResult(ok=False, error="O'z rolingizni pasaytira olmaysiz")
    if _would_remove_last_owner(db, user, new_role=role, new_active=user.is_active):
        return UserChangeResult(ok=False, error=LAST_OWNER_ERROR)

    previous = user.role
    user.role = role.value
    if _owner_invariant_broken(db):
        user.role = previous
        db.flush()
        return UserChangeResult(ok=False, error=LAST_OWNER_ERROR)
    return UserChangeResult(ok=True, user=user)


def set_active(db: Session, user: AdminUser, active: bool, *, actor: AdminIdentity) -> UserChangeResult:
    if user.id == actor.user_id and not active:
        return UserChangeResult(ok=False, error="O'zingizni o'chira olmaysiz")
    if _would_remove_last_owner(db, user, new_role=user.admin_role, new_active=active):
        return UserChangeResult(ok=False, error="Oxirgi faol egani o'chirib bo'lmaydi")

    previous = user.is_active
    user.is_active = active
    if _owner_invariant_broken(db):
        user.is_active = previous
        db.flush()
        return UserChangeResult(ok=False, error="Oxirgi faol egani o'chirib bo'lmaydi")
    return UserChangeResult(ok=True, user=user)


def _owner_invariant_broken(db: Session) -> bool:
    """O'zgarishdan KEYIN yana bir marta tekshiradi.

    Oldindan tekshirish yolg'iz o'zi yetarli emas: ikki admin bir vaqtda ikki xil
    egani pasaytirsa, ikkalasi ham "boshqa ega bor" deb ko'rib o'tib ketardi va
    natijada bitta ham faol ega qolmasdi. Bu tekshiruv o'sha tranzaksiyaning
    o'zida bajariladi, ya'ni yozuvdan keyingi holatni ko'radi.
    """
    db.flush()
    return AdminRepository(db).count_active_owners() == 0


def _would_remove_last_owner(db: Session, user: AdminUser, *, new_role: AdminRole, new_active: bool) -> bool:
    """Panelga kirish yo'lini butunlay yopib qo'yishning oldini oladi."""
    was_owner = user.admin_role == AdminRole.OWNER and user.is_active
    stays_owner = new_role == AdminRole.OWNER and new_active
    if not was_owner or stays_owner:
        return False
    return AdminRepository(db).count_active_owners(exclude_id=user.id) == 0


def has_active_owner(db: Session) -> bool:
    return AdminRepository(db).count_active_owners() > 0

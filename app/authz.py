"""Admin rollari va ruxsatlari — veb panel va bot uchun YAGONA manba.

Ruxsat tekshiruvi bitta joyda bajariladi (`app.dependencies.require_admin`), lekin
har endpoint qaysi ruxsatni talab qilishini o'zi e'lon qiladi. E'lon qilmagan
endpoint ochiq qolmaydi, balki 403 beradi — ya'ni yangi marshrut qo'shib ruxsatni
belgilashni unutish "hamma ko'ra oladi" degani emas.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from app.models.enums import AdminRole

# --- Ruxsatlar ---
# Ataylab ikkiga ajratilgan: agregat ko'rsatkichlar shaxsiy ma'lumot emas,
# sessiya tafsiloti va chek rasmi esa aynan shaxsiy ma'lumot.
VIEW_AGGREGATE = "view_aggregate"
VIEW_PII = "view_pii"
MODERATE_PAYMENTS = "moderate_payments"
EXPORT_DATA = "export_data"
VIEW_OPS = "view_ops"
MANAGE_USERS = "manage_users"
VIEW_AUDIT = "view_audit"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        VIEW_AGGREGATE,
        VIEW_PII,
        MODERATE_PAYMENTS,
        EXPORT_DATA,
        VIEW_OPS,
        MANAGE_USERS,
        VIEW_AUDIT,
    }
)

PERMISSIONS: dict[AdminRole, frozenset[str]] = {
    AdminRole.VIEWER: frozenset({VIEW_AGGREGATE}),
    AdminRole.MODERATOR: frozenset({VIEW_AGGREGATE, VIEW_PII, MODERATE_PAYMENTS, EXPORT_DATA, VIEW_OPS}),
    AdminRole.OWNER: ALL_PERMISSIONS,
}

ROLE_LABELS: dict[AdminRole, str] = {
    AdminRole.OWNER: "Egasi",
    AdminRole.MODERATOR: "Moderator",
    AdminRole.VIEWER: "Kuzatuvchi",
}


ACTOR_WEB = "web"
ACTOR_TELEGRAM = "telegram"
ACTOR_CLI = "cli"
ACTOR_SYSTEM = "system"


@dataclass(frozen=True)
class AdminIdentity:
    """Bir so'rov (yoki bitta bot chaqiruvi) davomida amal qiluvchi admin shaxsi.

    `user_id` None bo'lishi mumkin: `.env` dagi zaxira hisob va `ADMIN_TELEGRAM_IDS`
    ro'yxatidagi ID lar bazada qatorga ega emas. Ular har doim OWNER huquqida ishlaydi —
    bu ataylab: zaxira hisob panelga kira olmay qolish holatidan chiqarish uchun bor.
    """

    username: str
    role: AdminRole
    user_id: int | None = None
    telegram_user_id: int | None = None
    actor_type: str = ACTOR_WEB

    @property
    def audit_actor(self) -> str:
        return f"{self.actor_type}:{self.username}"

    def can(self, permission: str) -> bool:
        return has_permission(self.role, permission)


def has_permission(role: AdminRole, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, frozenset())


def role_label(role: AdminRole) -> str:
    return ROLE_LABELS.get(role, role.value)


# --- Endpoint -> ruxsat reyestri ---
# Kalit sifatida funksiyaning o'zi ishlatiladi: FastAPI `request.scope["route"].endpoint`
# da aynan shu obyektni beradi, shuning uchun nom to'qnashuvi bo'lmaydi.
_REGISTRY: dict[Callable[..., object], str] = {}

F = TypeVar("F", bound=Callable[..., object])


def requires(permission: str) -> Callable[[F], F]:
    """Endpoint uchun kerakli ruxsatni e'lon qiladi.

    Dekorator funksiyani o'ramaydi — faqat reyestrga yozadi, shuning uchun
    FastAPI ning signatura tahlili (Depends, Form, Query) o'zgarmaydi.
    """
    if permission not in ALL_PERMISSIONS:
        raise ValueError(f"Noma'lum ruxsat: {permission}")

    def decorate(func: F) -> F:
        _REGISTRY[func] = permission
        return func

    return decorate


def required_permission(endpoint: Callable[..., object] | None) -> str | None:
    if endpoint is None:
        return None
    return _REGISTRY.get(endpoint)


def registered_endpoints() -> frozenset[Callable[..., object]]:
    return frozenset(_REGISTRY)

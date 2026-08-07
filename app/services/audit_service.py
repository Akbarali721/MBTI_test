"""Audit jurnaliga yozish — bitta darvoza.

Ikkita qoida shu modulda majburlanadi:

1. Yozuvda faqat identifikator va qisqa izoh bo'ladi. Sessiya tokeni, to'lov kodi,
   ulashish kodi yoki chek `file_id` — bularning har biri o'zi kirish huquqi, ya'ni
   jurnalni o'qigan odam mijoz natijasini ocha oladigan bo'lib qolardi.
2. Pul va rol qarorlariga tegishli yozuvlar hech qachon avtomatik tozalanmaydi.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.authz import ACTOR_SYSTEM, AdminIdentity
from app.repositories.admin_repository import AdminRepository

logger = logging.getLogger(__name__)

# --- Harakat nomlari ---
LOGIN_SUCCESS = "login_success"
LOGIN_FAILED = "login_failed"
LOGOUT = "logout"
PERMISSION_DENIED = "permission_denied"
PAYMENT_APPROVED = "payment_approved"
PAYMENT_REJECTED = "payment_rejected"
PREMIUM_GRANTED = "premium_granted"
EXPORT_SESSIONS = "export_sessions"
EXPORT_PAYMENTS = "export_payments"
USER_CREATED = "user_created"
USER_ROLE_CHANGED = "user_role_changed"
USER_ACTIVATED = "user_activated"
USER_DEACTIVATED = "user_deactivated"
USER_PASSWORD_CHANGED = "user_password_changed"
NOTIFICATION_RETRIED = "notification_retried"
RETENTION_RUN = "retention_run"

# Buxgalteriya va javobgarlik uchun kerak bo'ladigan yozuvlar. Saqlash siyosati
# ularga tegmaydi — muddat sozlamasi qanchalik qisqa bo'lsa ham.
NEVER_PURGED_ACTIONS: frozenset[str] = frozenset(
    {
        PAYMENT_APPROVED,
        PAYMENT_REJECTED,
        PREMIUM_GRANTED,
        EXPORT_SESSIONS,
        EXPORT_PAYMENTS,
        USER_CREATED,
        USER_ROLE_CHANGED,
        USER_ACTIVATED,
        USER_DEACTIVATED,
        USER_PASSWORD_CHANGED,
        RETENTION_RUN,
    }
)

# Uzun heks satr — bu deyarli har doim token yoki file_id.
_SECRET_LIKE = re.compile(r"[A-Fa-f0-9]{24,}")
_VALUE_MAX = 80


def _clean_value(value: object) -> str:
    text = str(value)
    if _SECRET_LIKE.search(text):
        # Ataylab qiymatni tashlab yuboramiz: jurnal kirish huquqini tarqatmasligi kerak.
        return "<yashirildi>"
    text = " ".join(text.split())
    return text[:_VALUE_MAX]


def format_detail(fields: Mapping[str, object] | None) -> str | None:
    if not fields:
        return None
    parts = [f"{key}={_clean_value(value)}" for key, value in fields.items() if value is not None]
    return "; ".join(parts) or None


def record(
    db: Session,
    actor: AdminIdentity | None,
    action: str,
    *,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: Mapping[str, object] | None = None,
) -> None:
    """Yozuvni joriy tranzaksiyaga qo'shadi (commit chaqiruvchida).

    Muvaffaqiyatli harakat uchun bu to'g'ri: harakat rollback bo'lsa, uni tasdiqlagan
    yozuv ham qolmaydi.
    """
    text = format_detail(detail)
    AdminRepository(db).add_audit(
        actor_type=actor.actor_type if actor else ACTOR_SYSTEM,
        actor_label=actor.username if actor else "system",
        actor_id=actor.user_id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=text,
    )
    # Jurnal bazadan tashqarida ham iz qoldirsin.
    logger.info(
        "audit: %s %s target=%s/%s %s",
        actor.audit_actor if actor else "system",
        action,
        target_type or "-",
        target_id if target_id is not None else "-",
        text or "",
    )

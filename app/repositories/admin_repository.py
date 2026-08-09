"""Admin hisoblari va audit jurnali bilan ishlash."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.admin import AUDIT_DETAIL_MAX, AdminAuditLog, AdminUser
from app.models.enums import AdminRole


def normalize_username(value: str | None) -> str:
    """Login har doim kichik harflarda saqlanadi va shu ko'rinishda qidiriladi.

    Aks holda 'Erkin' va 'erkin' ikkita alohida hisob bo'lib qolardi, katta-kichik
    harf bilan kirish esa "parol noto'g'ri" deb tushunilardi.
    """
    return (value or "").strip().lower()


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> AdminUser | None:
        return self.db.get(AdminUser, user_id)

    def get_by_username(self, username: str) -> AdminUser | None:
        cleaned = normalize_username(username)
        if not cleaned:
            return None
        return self.db.scalar(select(AdminUser).where(AdminUser.username == cleaned))

    def get_by_telegram_id(self, telegram_user_id: int) -> AdminUser | None:
        return self.db.scalar(select(AdminUser).where(AdminUser.telegram_user_id == telegram_user_id))

    def list_users(self) -> list[AdminUser]:
        stmt = select(AdminUser).order_by(desc(AdminUser.is_active), AdminUser.username)
        return list(self.db.scalars(stmt).all())

    def count_active_owners(self, *, exclude_id: int | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(AdminUser)
            .where(AdminUser.role == AdminRole.OWNER.value, AdminUser.is_active.is_(True))
        )
        if exclude_id is not None:
            stmt = stmt.where(AdminUser.id != exclude_id)
        return int(self.db.scalar(stmt) or 0)

    def active_telegram_admins(self) -> dict[int, AdminUser]:
        stmt = select(AdminUser).where(AdminUser.is_active.is_(True), AdminUser.telegram_user_id.is_not(None))
        return {row.telegram_user_id: row for row in self.db.scalars(stmt).all() if row.telegram_user_id}

    def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role: AdminRole,
        telegram_user_id: int | None = None,
    ) -> AdminUser:
        user = AdminUser(
            username=normalize_username(username),
            password_hash=password_hash,
            role=role.value,
            telegram_user_id=telegram_user_id,
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def touch_login(self, user: AdminUser) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        self.db.flush()

    # --- Audit ---

    def add_audit(
        self,
        *,
        actor_type: str,
        actor_label: str,
        action: str,
        actor_id: int | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        detail: str | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            actor_type=actor_type,
            actor_label=actor_label[:64],
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=(detail or None) and detail[:AUDIT_DETAIL_MAX],
        )
        self.db.add(entry)
        return entry

    def list_audit(self, *, action: str | None = None, limit: int = 50, offset: int = 0) -> list:
        stmt = select(AdminAuditLog).order_by(desc(AdminAuditLog.created_at), desc(AdminAuditLog.id))
        if action and action != "all":
            stmt = stmt.where(AdminAuditLog.action == action)
        return list(self.db.scalars(stmt.offset(offset).limit(limit)).all())

    def count_audit(self, *, action: str | None = None) -> int:
        stmt = select(func.count()).select_from(AdminAuditLog)
        if action and action != "all":
            stmt = stmt.where(AdminAuditLog.action == action)
        return int(self.db.scalar(stmt) or 0)

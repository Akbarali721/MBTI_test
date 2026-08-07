"""Admin hisoblari va audit jurnali.

Hisoblar bazada saqlanadi, `.env` dagi ADMIN_USERNAME/ADMIN_PASSWORD_HASH esa zaxira
("break-glass") hisob bo'lib qoladi — shuning uchun mavjud deployʼlar hech qanday
sozlama o'zgartirmasdan ishlashda davom etadi.

Qatorlar HECH QACHON o'chirilmaydi, faqat `is_active=False` qilinadi: `approved_by`
va audit jurnalidagi yozuvlar foydalanuvchi nomiga tayanadi, o'chirilgan nom esa
qaytadan band qilinsa tarix boshqa odamga o'tib ketardi.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ADMIN_ROLE_VALUES, AdminRole

USERNAME_MAX = 64
USERNAME_PATTERN = r"^[a-z0-9._-]{3,32}$"
ADMIN_ROLE_CHECK_NAME = "ck_admin_users_role"

# Audit yozuvida faqat identifikator va qisqa izoh saqlanadi.
AUDIT_ACTION_MAX = 48
AUDIT_DETAIL_MAX = 500


def admin_role_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in ADMIN_ROLE_VALUES)
    return f"role IN ({values})"


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (CheckConstraint(admin_role_check_sql(), name=ADMIN_ROLE_CHECK_NAME),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Nom kichik harflarda saqlanadi: SQLite ham, Postgres ham String uchun
    # katta-kichik harfni ajratadi, ya'ni 'Erkin' va 'erkin' aks holda ikki hisob bo'lardi.
    username: Mapped[str] = mapped_column(String(USERNAME_MAX), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default=AdminRole.MODERATOR.value, nullable=False)
    # Telegramda moderatsiya qiladigan admin shu ustun orqali tanib olinadi.
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def admin_role(self) -> AdminRole:
        try:
            return AdminRole(self.role)
        except ValueError:
            # Noma'lum rol eng kam huquqqa tushiriladi — CHECK cheklovi buni oldini oladi,
            # lekin qo'lda o'zgartirilgan qator ham xavfsiz qolishi kerak.
            return AdminRole.VIEWER


class AdminAuditLog(Base):
    """Faqat qo'shib boriladigan jurnal: kim, qachon, nima qildi.

    Ilovada bu jadvalni UPDATE yoki DELETE qiladigan yo'l yo'q (saqlash siyosatining
    cheklangan tozalashidan tashqari, u ham faqat CLI orqali).
    """

    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 'web' | 'telegram' | 'cli' | 'system'
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # Yozuv vaqtidagi ko'rinadigan nom (keyin o'zgarsa ham tarix o'zgarmaydi).
    actor_label: Mapped[str] = mapped_column(String(USERNAME_MAX), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(AUDIT_ACTION_MAX), index=True, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Faqat qisqa, ruxsat etilgan qiymatlar. Token, to'lov kodi, ulashish kodi,
    # chek file_id va hech qanday sir bu yerga yozilmaydi.
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

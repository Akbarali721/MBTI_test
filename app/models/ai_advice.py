"""AI yaratgan shaxsiy maslahatlar — premium bo'limining bir qismi.

Nima uchun alohida jadval, natija matnining yonida emas:

* Tashqi API pullik va sekin. Javob BIR MARTA yaratiladi va shu yerda qoladi;
  sahifa har ochilganda qayta so'ralsa hisob bir kunda bo'shab qolardi.
* Muvaffaqiyatsizlik ham yozuv: `status='failed'` va `attempts` bo'lmasa,
  foydalanuvchi tugmani cheksiz bosib har bosishda pul sarflardi.
* Sahifa render qilinishi tashqi xizmatga BOG'LIQ EMAS. Yozuv bo'lsa ko'rsatiladi,
  bo'lmasa tugma ko'rinadi — API o'lganda natija sahifasi baribir ochiladi.

`items` da faqat tayyor matn: model javobi TEKSHIRILGANDAN keyin (element soni,
uzunlik, boshqarish belgilari) saqlanadi. Shablon Jinja avtoescape bilan chiqaradi,
ya'ni model matni HTML sifatida bajarilmaydi.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

AI_ADVICE_STATUS_READY = "ready"
AI_ADVICE_STATUS_FAILED = "failed"
AI_ADVICE_STATUS_VALUES: tuple[str, ...] = (AI_ADVICE_STATUS_READY, AI_ADVICE_STATUS_FAILED)

AI_ADVICE_STATUS_CHECK_NAME = "ck_ai_advice_reports_status"

# `params` kabi: so'rov shakli o'zgarsa oshiriladi va eski yozuvlar qayta
# yaratilmaydi (lekin qaysi versiyada yaratilgani ko'rinib turadi).
AI_ADVICE_PROMPT_VERSION = 1


def ai_advice_status_check_sql() -> str:
    values = ", ".join(f"'{value}'" for value in AI_ADVICE_STATUS_VALUES)
    return f"status IN ({values})"


class AiAdviceReport(Base):
    __tablename__ = "ai_advice_reports"
    __table_args__ = (
        # Til bo'yicha alohida: interfeysni ruschaga o'tkazgan odam o'zbekcha
        # maslahatni ko'rmasligi kerak, lekin oldingi yozuv ham o'chmasligi kerak.
        UniqueConstraint("session_id", "language", name="uq_ai_advice_session_language"),
        CheckConstraint(ai_advice_status_check_sql(), name=AI_ADVICE_STATUS_CHECK_NAME),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("personality_test_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False, default=AI_ADVICE_PROMPT_VERSION)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Xarajatni ko'rish uchun: admin panelida qancha token ketgani ko'rinadi.
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @property
    def is_ready(self) -> bool:
        return self.status == AI_ADVICE_STATUS_READY and bool(self.items)

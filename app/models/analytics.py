"""Kunlik agregat: saqlash siyosati voronkani buzmasligi uchun.

Muammo: eskirgan VISITED sessiyalarni o'chirish voronkaning FAQAT yuqori qismini
yo'qotadi. Natijada 30 kundan eski har qanday oyna uchun "tugatish foizi" 100% ga
yaqinlashadi va A/B qarori noto'g'ri to'plam foydasiga hal bo'ladi.

Yechim: o'chirishdan OLDIN o'sha kunlar bitta qatorga yig'iladi. Voronka tirik
qatorlarni shu agregat bilan qo'shib hisoblaydi, ya'ni tarixiy sonlar o'zgarmaydi.
Agregatda shaxsiy ma'lumot yo'q (faqat kun, to'plam va sanoqlar), shuning uchun uni
cheksiz saqlash mumkin.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.personality import DEFAULT_VARIANT

SESSION_DAILY_UNIQUE = "uq_session_daily_stats_day_variant"

# Agregat ustunlari — voronka bosqichlari bilan bir xil tartibda.
STAGE_COLUMNS: tuple[str, ...] = (
    "visited",
    "started",
    "completed",
    "payment_started",
    "receipt_sent",
    "approved",
)


class SessionDailyStats(Base):
    __tablename__ = "session_daily_stats"
    __table_args__ = (UniqueConstraint("day", "variant", name=SESSION_DAILY_UNIQUE),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Toshkent kun boshining UTC lahzasi — dashboard'dagi "bugun" bilan bir xil chegara.
    day: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    variant: Mapped[str] = mapped_column(String(8), nullable=False, default=DEFAULT_VARIANT)
    visited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    receipt_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

"""Telegram foydalanuvchi profili — bot va WebApp orasidagi yagona shaxs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    telegram_last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bot_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    phone_shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    premium_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    referrals_made: Mapped[list["TelegramReferral"]] = relationship(
        back_populates="referrer",
        foreign_keys="TelegramReferral.referrer_telegram_user_id",
    )
    referral_received: Mapped["TelegramReferral | None"] = relationship(
        back_populates="referred",
        foreign_keys="TelegramReferral.referred_telegram_user_id",
        uselist=False,
    )


class TelegramReferral(Base):
    __tablename__ = "telegram_referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_telegram_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("telegram_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_telegram_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("telegram_users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    referred_session_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("personality_test_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    referrer: Mapped["TelegramUser"] = relationship(
        back_populates="referrals_made",
        foreign_keys=[referrer_telegram_user_id],
    )
    referred: Mapped["TelegramUser"] = relationship(
        back_populates="referral_received",
        foreign_keys=[referred_telegram_user_id],
    )

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AppearanceTheme, PersonalityDimension, PersonalitySessionStatus

if TYPE_CHECKING:
    # Modullar bir-biriga havola qiladi: import faqat tipni tekshirishda bajariladi.
    from app.models.payment_request import PaymentRequest

DEFAULT_CONTENT_LANGUAGE = "uz"
# A/B test bo'lmasa hamma narsa shu to'plamda ishlaydi.
DEFAULT_VARIANT = "A"


def _enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """Postgres enum labellari a'zo nomi emas, qiymati bo'lishi uchun."""
    return [str(member.value) for member in enum_class]


class PersonalityTestSession(Base):
    __tablename__ = "personality_test_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    payment_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True, nullable=True)
    # Ommaviy ulashish kodi: tokendan mustaqil, chunki token — natijaga to'liq kirish huquqi.
    share_code: Mapped[str | None] = mapped_column(String(24), unique=True, index=True, nullable=True)
    # Qaysi savol to'plami ko'rsatilgani — A/B natijalarini ajratish uchun.
    variant: Mapped[str] = mapped_column(
        String(8), default=DEFAULT_VARIANT, server_default=DEFAULT_VARIANT, nullable=False, index=True
    )
    status: Mapped[PersonalitySessionStatus] = mapped_column(
        Enum(
            PersonalitySessionStatus,
            name="personality_session_status",
            values_callable=_enum_values,
        ),
        default=PersonalitySessionStatus.VISITED,
        nullable=False,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_type: Mapped[str | None] = mapped_column(String(4), nullable=True)
    e_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    i_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    s_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    n_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    t_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    f_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    j_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    p_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    premium_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    premium_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    premium_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    appearance_theme: Mapped[AppearanceTheme | None] = mapped_column(
        Enum(AppearanceTheme, name="appearance_theme", values_callable=_enum_values),
        nullable=True,
        default=None,
    )
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["PersonalityAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    payment_requests: Mapped[list["PaymentRequest"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class PersonalityQuestion(Base):
    __tablename__ = "personality_questions"
    # A/B test uchun bir nechta savol to'plami: tartib raqami to'plam ichida noyob.
    __table_args__ = (UniqueConstraint("variant", "order_number", name="uq_question_variant_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    dimension: Mapped[PersonalityDimension] = mapped_column(
        Enum(PersonalityDimension, name="personality_dimension", values_callable=_enum_values),
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(
        String(8), default=DEFAULT_VARIANT, server_default=DEFAULT_VARIANT, nullable=False, index=True
    )
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    options: Mapped[list["PersonalityOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="PersonalityOption.order_number"
    )


class PersonalityOption(Base):
    __tablename__ = "personality_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("personality_questions.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    e_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    i_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    s_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    n_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    t_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    f_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    j_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    p_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped["PersonalityQuestion"] = relationship(back_populates="options")


class PersonalityAnswer(Base):
    __tablename__ = "personality_answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_personality_answer_session_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("personality_test_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("personality_questions.id", ondelete="CASCADE"), nullable=False
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("personality_options.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["PersonalityTestSession"] = relationship(back_populates="answers")


class PersonalityResultContent(Base):
    __tablename__ = "personality_result_contents"
    __table_args__ = (
        UniqueConstraint("personality_type", "language", name="uq_result_content_type_language"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personality_type: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    language: Mapped[str] = mapped_column(
        String(5), default=DEFAULT_CONTENT_LANGUAGE, server_default=DEFAULT_CONTENT_LANGUAGE, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    free_strengths: Mapped[str] = mapped_column(Text, nullable=False)
    free_challenges: Mapped[str] = mapped_column(Text, nullable=False)
    public_view: Mapped[str] = mapped_column(Text, nullable=False)
    motivation_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    work_style: Mapped[str] = mapped_column(Text, nullable=False)
    career_environment: Mapped[str] = mapped_column(Text, nullable=False)
    friendship_style: Mapped[str] = mapped_column(Text, nullable=False)
    relationship_needs: Mapped[str] = mapped_column(Text, nullable=False)
    compatible_people: Mapped[str] = mapped_column(Text, nullable=False)
    difficult_communication: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

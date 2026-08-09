from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.personality import PersonalityTestSession

TEAM_NAME_MAX = 80
MEMBER_NAME_MAX = 80


class Team(Base):
    """HR/jamoa rejimi: bir nechta xodimning natijasi bitta panelda.

    Ikkita kod bor va ular ataylab ajratilgan: invite_code havolada tarqaladi,
    manage_code esa faqat egasida qoladi — havolani olgan xodim panelni ko'ra olmaydi.
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(TEAM_NAME_MAX), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    manage_code: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["TeamMember"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="TeamMember.joined_at",
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        # Bitta sessiya bitta jamoada faqat bir marta hisoblanadi.
        UniqueConstraint("team_id", "session_id", name="uq_team_members_team_session"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("personality_test_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(MEMBER_NAME_MAX), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped["Team"] = relationship(back_populates="members")
    session: Mapped["PersonalityTestSession"] = relationship()

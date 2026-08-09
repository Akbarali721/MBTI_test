"""Jamoa rejimi: a'zolarni yig'ish va tarkibni tahlil qilish."""

from __future__ import annotations

import secrets
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.models.team import MEMBER_NAME_MAX, TEAM_NAME_MAX, Team, TeamMember

CODE_BYTES = 9
MAX_MEMBERS = 200

# Ogohlantirish chegarasi: qutb ulushi shundan oshsa, jamoa bir tomonga qiyshaygan.
SKEW_THRESHOLD = 0.75
_POLE_PAIRS = (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))


@dataclass(frozen=True)
class PoleBalance:
    left_letter: str
    right_letter: str
    left_count: int
    right_count: int

    @property
    def total(self) -> int:
        return self.left_count + self.right_count

    @property
    def left_percent(self) -> int:
        return round(self.left_count / self.total * 100) if self.total else 50

    @property
    def right_percent(self) -> int:
        return 100 - self.left_percent if self.total else 50

    @property
    def dominant_letter(self) -> str | None:
        if not self.total:
            return None
        share = max(self.left_count, self.right_count) / self.total
        if share < SKEW_THRESHOLD:
            return None
        return self.left_letter if self.left_count >= self.right_count else self.right_letter

    @property
    def missing_letter(self) -> str | None:
        if not self.total:
            return None
        if self.left_count == 0:
            return self.left_letter
        if self.right_count == 0:
            return self.right_letter
        return None


@dataclass(frozen=True)
class TeamMemberView:
    display_name: str
    result_type: str
    joined_at: object


@dataclass(frozen=True)
class TeamComposition:
    members: tuple[TeamMemberView, ...]
    type_counts: tuple[tuple[str, int], ...]
    balances: tuple[PoleBalance, ...]

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def distinct_types(self) -> int:
        return len(self.type_counts)


def _new_code() -> str:
    return secrets.token_urlsafe(CODE_BYTES)


def _unique_code(db: Session, column) -> str:
    for _ in range(5):
        code = _new_code()
        if db.scalar(select(Team.id).where(column == code)) is None:
            return code
    return secrets.token_urlsafe(CODE_BYTES * 2)


def create_team(db: Session, name: str) -> Team:
    cleaned = (name or "").strip()[:TEAM_NAME_MAX]
    if not cleaned:
        raise ValueError("Jamoa nomi bo'sh bo'lishi mumkin emas")
    team = Team(
        name=cleaned,
        invite_code=_unique_code(db, Team.invite_code),
        manage_code=_unique_code(db, Team.manage_code),
    )
    db.add(team)
    db.flush()
    db.refresh(team)
    return team


def team_by_invite(db: Session, invite_code: str) -> Team | None:
    code = (invite_code or "").strip()
    return db.scalar(select(Team).where(Team.invite_code == code)) if code else None


def team_by_manage(db: Session, manage_code: str) -> Team | None:
    code = (manage_code or "").strip()
    return db.scalar(select(Team).where(Team.manage_code == code)) if code else None


def add_member(
    db: Session, team: Team, session: PersonalityTestSession, display_name: str
) -> TeamMember | None:
    """Bir sessiya bir jamoada bir marta; nom bo'sh bo'lsa sessiya kodi ishlatiladi."""
    existing = db.scalar(
        select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.session_id == session.id)
    )
    cleaned = (display_name or "").strip()[:MEMBER_NAME_MAX] or (session.payment_code or "—")
    if existing is not None:
        existing.display_name = cleaned
        db.flush()
        return existing

    if db.scalar(select(TeamMember.id).where(TeamMember.team_id == team.id).limit(1)) is not None:
        count = len(team.members)
        if count >= MAX_MEMBERS:
            return None

    member = TeamMember(team_id=team.id, session_id=session.id, display_name=cleaned)
    db.add(member)
    db.flush()
    return member


def _load_members(db: Session, team: Team) -> list[TeamMember]:
    stmt = (
        select(TeamMember)
        .options(joinedload(TeamMember.session))
        .where(TeamMember.team_id == team.id)
        .order_by(TeamMember.joined_at, TeamMember.id)
    )
    return list(db.scalars(stmt).all())


def composition(db: Session, team: Team) -> TeamComposition:
    # A'zo faqat tugallangan sessiya bilan qo'shiladi, ammo natija keyin qayta
    # hisoblanishi mumkin — shuning uchun tarkib baribir filtrlanadi.
    rows = [
        row
        for row in _load_members(db, team)
        if row.session.status == PersonalitySessionStatus.COMPLETED and row.session.result_type
    ]
    members = tuple(
        TeamMemberView(
            display_name=row.display_name,
            result_type=row.session.result_type or "",
            joined_at=row.joined_at,
        )
        for row in rows
    )

    counter = Counter(member.result_type for member in members)
    # Ko'p uchraganidan kamiga, teng bo'lsa alifbo tartibida — chiqish barqaror bo'lsin.
    type_counts = tuple(sorted(counter.items(), key=lambda item: (-item[1], item[0])))

    balances = tuple(
        PoleBalance(
            left_letter=left,
            right_letter=right,
            left_count=sum(1 for m in members if m.result_type[index] == left),
            right_count=sum(1 for m in members if m.result_type[index] == right),
        )
        for index, (left, right) in enumerate(_POLE_PAIRS)
    )

    return TeamComposition(members=members, type_counts=type_counts, balances=balances)

"""Natija fikrini saqlash va admin ro‘yxati."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.personality import PersonalityResultUserFeedback, PersonalityTestSession
from app.models.telegram_user import TelegramUser
from app.personality.user_feedback_constants import (
    USER_FEEDBACK_MAX_COMMENT_LEN,
    USER_FEEDBACK_RATING_VALUES,
)
from app.timeutils import utcnow


@dataclass(frozen=True)
class UserFeedbackStats:
    total: int
    positive: int
    partial: int
    negative: int

    def percent(self, count: int) -> int:
        if self.total <= 0:
            return 0
        return round(100 * count / self.total)


@dataclass(frozen=True)
class AdminFeedbackRow:
    id: int
    created_at: datetime
    rating: str
    comment: str | None
    result_type: str | None
    telegram_id: int | None
    telegram_username: str | None
    session_token: str


class ResultUserFeedbackService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_session(self, session_id: int) -> PersonalityResultUserFeedback | None:
        return self.db.scalar(
            select(PersonalityResultUserFeedback).where(
                PersonalityResultUserFeedback.session_id == session_id
            )
        )

    def upsert(
        self,
        session: PersonalityTestSession,
        *,
        rating: str,
        comment: str | None,
    ) -> PersonalityResultUserFeedback:
        if rating not in USER_FEEDBACK_RATING_VALUES:
            raise ValueError("invalid rating")
        cleaned = (comment or "").strip()
        if len(cleaned) > USER_FEEDBACK_MAX_COMMENT_LEN:
            raise ValueError("comment too long")
        text: str | None = cleaned or None

        telegram_pk: int | None = None
        if session.telegram_user_id:
            telegram_pk = self.db.scalar(
                select(TelegramUser.id).where(TelegramUser.telegram_id == session.telegram_user_id)
            )

        row = self.get_for_session(session.id)
        now = utcnow()
        if row is None:
            row = PersonalityResultUserFeedback(
                session_id=session.id,
                telegram_user_id=telegram_pk,
                rating=rating,
                comment=text,
                created_at=now,
                updated_at=now,
            )
            self.db.add(row)
        else:
            row.rating = rating
            row.comment = text
            row.updated_at = now
            if telegram_pk is not None:
                row.telegram_user_id = telegram_pk
        self.db.flush()
        return row

    def stats(self) -> UserFeedbackStats:
        rows = self.db.execute(
            select(PersonalityResultUserFeedback.rating, func.count()).group_by(
                PersonalityResultUserFeedback.rating
            )
        ).all()
        counts = {rating: int(n) for rating, n in rows}
        positive = counts.get("positive", 0)
        partial = counts.get("partial", 0)
        negative = counts.get("negative", 0)
        total = positive + partial + negative
        return UserFeedbackStats(
            total=total,
            positive=positive,
            partial=partial,
            negative=negative,
        )

    def list_recent(self, *, limit: int = 200) -> list[AdminFeedbackRow]:
        stmt = (
            select(PersonalityResultUserFeedback)
            .options(joinedload(PersonalityResultUserFeedback.session))
            .order_by(PersonalityResultUserFeedback.created_at.desc())
            .limit(limit)
        )
        feedback_rows = list(self.db.scalars(stmt).unique().all())
        out: list[AdminFeedbackRow] = []
        for fb in feedback_rows:
            session = fb.session
            tg_id = session.telegram_user_id if session else None
            tg_name = session.telegram_username if session else None
            out.append(
                AdminFeedbackRow(
                    id=fb.id,
                    created_at=fb.created_at,
                    rating=fb.rating,
                    comment=fb.comment,
                    result_type=session.result_type if session else None,
                    telegram_id=tg_id,
                    telegram_username=tg_name,
                    session_token=session.token if session else "",
                )
            )
        return out

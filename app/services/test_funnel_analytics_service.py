"""Test savol voronkasi va savol bo'yicha drop-off analitikasi."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.personality.constants import SESSION_QUESTION_COUNT

MILESTONE_QUESTIONS: tuple[int, ...] = (1, 5, 10, 15, 20, 24)


@dataclass(frozen=True)
class TestFunnelStage:
    key: str
    label: str
    count: int
    of_first: float
    of_previous: float
    drop_off_pct: float


@dataclass(frozen=True)
class QuestionDropOffRow:
    question_number: int
    reached: int
    continued: int
    drop_off: int
    drop_off_pct: float


@dataclass(frozen=True)
class TestFunnelReport:
    stages: list[TestFunnelStage]
    question_drop_offs: list[QuestionDropOffRow]
    top_drop_offs: list[QuestionDropOffRow]


class SessionTestFunnelAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def report(self) -> TestFunnelReport:
        started = self._count_started()
        milestone_counts = [started]
        for q in MILESTONE_QUESTIONS:
            milestone_counts.append(self._count_reached_at_least(q))
        completed = self._count_completed()
        milestone_counts.append(completed)

        labels = [
            "Test boshlangan",
            *[f"{q}-savol" for q in MILESTONE_QUESTIONS],
            "Tugatgan",
        ]
        keys = ["started", *[f"q{q}" for q in MILESTONE_QUESTIONS], "completed"]

        stages: list[TestFunnelStage] = []
        first = milestone_counts[0] or 1
        prev_count = milestone_counts[0]
        for idx, (key, label, count) in enumerate(zip(keys, labels, milestone_counts, strict=True)):
            of_first = round(count / first * 100, 1) if first else 0.0
            of_previous = round(count / prev_count * 100, 1) if prev_count else 0.0
            drop = round((1 - count / prev_count) * 100, 1) if idx > 0 and prev_count else 0.0
            stages.append(
                TestFunnelStage(
                    key=key,
                    label=label,
                    count=count,
                    of_first=of_first,
                    of_previous=of_previous,
                    drop_off_pct=drop,
                )
            )
            prev_count = count

        question_rows = self._question_drop_offs()
        top = sorted(question_rows, key=lambda row: (-row.drop_off_pct, -row.drop_off))[:5]
        return TestFunnelReport(stages=stages, question_drop_offs=question_rows, top_drop_offs=top)

    def _base_started_filter(self):
        return (
            PersonalityTestSession.started_at.is_not(None),
            PersonalityTestSession.anonymized_at.is_(None),
        )

    def _count_started(self) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(*self._base_started_filter())
        )
        return int(self.db.scalar(stmt) or 0)

    def _count_completed(self) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(
                *self._base_started_filter(),
                PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def _count_reached_at_least(self, question_number: int) -> int:
        total_default = SESSION_QUESTION_COUNT
        stmt = (
            select(func.count())
            .select_from(PersonalityTestSession)
            .where(
                *self._base_started_filter(),
                or_(
                    PersonalityTestSession.max_question_reached >= question_number,
                    PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
                    PersonalityTestSession.answered_questions >= question_number,
                ),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def _question_drop_offs(self) -> list[QuestionDropOffRow]:
        total = SESSION_QUESTION_COUNT
        rows: list[QuestionDropOffRow] = []
        for q in range(1, total + 1):
            reached = self._count_reached_at_least(q)
            if q < total:
                continued = self._count_reached_at_least(q + 1)
            else:
                continued = self._count_completed()
            drop = max(reached - continued, 0)
            pct = round(drop / reached * 100, 1) if reached else 0.0
            rows.append(
                QuestionDropOffRow(
                    question_number=q,
                    reached=reached,
                    continued=continued,
                    drop_off=drop,
                    drop_off_pct=pct,
                )
            )
        return rows

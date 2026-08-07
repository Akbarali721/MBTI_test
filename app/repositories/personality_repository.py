import json
import uuid
from datetime import datetime, timezone
from typing import Any, cast

from sqlalchemy import Table, func, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.enums import AppearanceTheme, PersonalitySessionStatus
from app.models.personality import (
    DEFAULT_CONTENT_LANGUAGE,
    DEFAULT_VARIANT,
    PersonalityAnswer,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityResultContent,
    PersonalityTestSession,
)
from app.personality.payment_code import generate_payment_code
from app.personality.share_code import generate_share_code
from app.personality.variants import choose_variant, normalize_variant
from app.services.personality_scoring import calculate_personality_result

SCORE_KEYS = ("e", "i", "s", "n", "t", "f", "j", "p")


class PersonalityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(
        self,
        *,
        user_id: int | None = None,
        telegram_user_id: int | None = None,
        source: str | None = None,
        status: PersonalitySessionStatus = PersonalitySessionStatus.VISITED,
        variant: str | None = None,
    ) -> PersonalityTestSession:
        now = datetime.now(timezone.utc)
        # Variant sessiya yaratilganda bir marta tanlanadi va o'zgarmaydi.
        chosen = normalize_variant(variant) if variant else choose_variant(settings.question_variants)
        total = self.count_active_questions(chosen)
        token = uuid.uuid4().hex
        session = PersonalityTestSession(
            token=token,
            payment_code=generate_payment_code(self.db, token),
            share_code=generate_share_code(self.db),
            variant=chosen,
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            status=status,
            current_question_index=0,
            total_questions=total,
            answered_questions=0,
            source=source,
            last_activity_at=now,
        )
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)
        return session

    def touch_session_activity(self, session: PersonalityTestSession) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        self.db.flush()

    def set_source_if_empty(self, session: PersonalityTestSession, source: str) -> None:
        if session.source or not source:
            return
        session.source = source
        self.db.flush()

    def count_answers(self, session_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalityAnswer)
            .where(PersonalityAnswer.session_id == session_id)
        )
        return int(self.db.scalar(stmt) or 0)

    def _apply_answer_analytics(self, session: PersonalityTestSession) -> None:
        now = datetime.now(timezone.utc)
        count = self.count_answers(session.id)
        session.answered_questions = count
        session.last_activity_at = now
        if count == 0:
            self.db.flush()
            return
        if session.status == PersonalitySessionStatus.VISITED:
            session.status = PersonalitySessionStatus.STARTED
            session.started_at = session.started_at or now
        elif session.status == PersonalitySessionStatus.STARTED and count >= 2:
            session.status = PersonalitySessionStatus.IN_PROGRESS
        self.db.flush()

    def get_session_by_token(self, token: str) -> PersonalityTestSession | None:
        stmt = select(PersonalityTestSession).where(PersonalityTestSession.token == token)
        return self.db.scalar(stmt)

    def get_session_by_id(self, session_id: int) -> PersonalityTestSession | None:
        return self.db.get(PersonalityTestSession, session_id)

    def get_completed_sessions_by_tokens(self, tokens: list[str]) -> list[PersonalityTestSession]:
        """Tarix sahifasi uchun: bitta so'rov, eng eskisidan boshlab tartiblangan."""
        if not tokens:
            return []
        stmt = (
            select(PersonalityTestSession)
            .where(
                PersonalityTestSession.token.in_(tokens),
                PersonalityTestSession.status == PersonalitySessionStatus.COMPLETED,
            )
            .order_by(PersonalityTestSession.completed_at.asc(), PersonalityTestSession.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_sessions(self, limit: int = 200) -> list[PersonalityTestSession]:
        stmt = select(PersonalityTestSession).order_by(PersonalityTestSession.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_active_questions(self, variant: str = DEFAULT_VARIANT) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalityQuestion)
            .where(
                PersonalityQuestion.is_active.is_(True),
                PersonalityQuestion.variant == variant,
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def get_active_questions_ordered(self, variant: str = DEFAULT_VARIANT) -> list[PersonalityQuestion]:
        stmt = (
            select(PersonalityQuestion)
            .where(
                PersonalityQuestion.is_active.is_(True),
                PersonalityQuestion.variant == variant,
            )
            .options(joinedload(PersonalityQuestion.options))
            .order_by(PersonalityQuestion.order_number)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_question_by_order(
        self, order_number: int, variant: str = DEFAULT_VARIANT
    ) -> PersonalityQuestion | None:
        stmt = (
            select(PersonalityQuestion)
            .where(
                PersonalityQuestion.is_active.is_(True),
                PersonalityQuestion.variant == variant,
                PersonalityQuestion.order_number == order_number,
            )
            .options(joinedload(PersonalityQuestion.options))
        )
        return self.db.scalar(stmt)

    def get_answer_map(self, session_id: int) -> dict[int, int]:
        stmt = select(PersonalityAnswer).where(PersonalityAnswer.session_id == session_id)
        answers = self.db.scalars(stmt).all()
        return {a.question_id: a.option_id for a in answers}

    def get_option(self, option_id: int) -> PersonalityOption | None:
        return self.db.get(PersonalityOption, option_id)

    def _dialect_upsert_answer(self, values: dict[str, int]) -> bool:
        """uq_personality_answer_session_question bo'yicha poyga holatisiz upsert."""
        table = cast(Table, PersonalityAnswer.__table__)
        dialect = self.db.get_bind().dialect.name
        if dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert

            stmt: Any = sqlite_insert(table).values(**values)
        elif dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            stmt = pg_insert(table).values(**values)
        else:
            return False

        self.db.execute(
            stmt.on_conflict_do_update(
                index_elements=[table.c.session_id, table.c.question_id],
                set_={"option_id": stmt.excluded.option_id},
            )
        )
        return True

    def upsert_answer(self, session_id: int, question_id: int, option_id: int) -> PersonalityAnswer:
        values = {"session_id": session_id, "question_id": question_id, "option_id": option_id}

        if not self._dialect_upsert_answer(values):
            existing = self.db.scalar(
                select(PersonalityAnswer).where(
                    PersonalityAnswer.session_id == session_id,
                    PersonalityAnswer.question_id == question_id,
                )
            )
            if existing:
                existing.option_id = option_id
            else:
                self.db.add(PersonalityAnswer(**values))
            self.db.flush()

        answer = self.db.scalar(
            select(PersonalityAnswer)
            .where(
                PersonalityAnswer.session_id == session_id,
                PersonalityAnswer.question_id == question_id,
            )
            .execution_options(populate_existing=True)
        )
        session = self.get_session_by_id(session_id)
        if session:
            self._apply_answer_analytics(session)
        return answer  # type: ignore[return-value]

    def score_totals_for_session(self, session_id: int) -> tuple[dict[str, int], int]:
        """Ballarni bitta JOIN + SUM so'rovi bilan hisoblaydi; (ballar, javoblar soni)."""
        columns = [
            func.coalesce(func.sum(getattr(PersonalityOption, f"{key}_score")), 0) for key in SCORE_KEYS
        ]
        stmt = (
            select(*columns, func.count(PersonalityAnswer.id))
            .select_from(PersonalityAnswer)
            .join(PersonalityOption, PersonalityOption.id == PersonalityAnswer.option_id)
            .where(PersonalityAnswer.session_id == session_id)
        )
        row = self.db.execute(stmt).one()
        totals = {key: int(row[index] or 0) for index, key in enumerate(SCORE_KEYS)}
        return totals, int(row[len(SCORE_KEYS)] or 0)

    def apply_scores(self, session: PersonalityTestSession, totals: dict[str, int]) -> str:
        result = calculate_personality_result(**totals)
        for key in SCORE_KEYS:
            setattr(session, f"{key}_score", totals[key])
        session.result_type = result.result_type
        return result.result_type

    def recalculate_and_complete_session(self, session: PersonalityTestSession) -> PersonalityTestSession:
        totals, answer_count = self.score_totals_for_session(session.id)
        self.apply_scores(session, totals)
        session.status = PersonalitySessionStatus.COMPLETED
        now = datetime.now(timezone.utc)
        session.completed_at = now
        session.last_activity_at = now
        session.answered_questions = session.total_questions or answer_count
        self.db.flush()
        self.db.refresh(session)
        return session

    def recompute_stored_sessions(self) -> int:
        """Saqlangan javoblardan barcha sessiya ballarini va result_type ni qayta hisoblaydi."""
        session_ids = list(
            self.db.scalars(
                select(PersonalityAnswer.session_id).distinct().order_by(PersonalityAnswer.session_id)
            ).all()
        )
        updated = 0
        for session_id in session_ids:
            session = self.get_session_by_id(session_id)
            if not session:
                continue
            totals, _ = self.score_totals_for_session(session_id)
            self.apply_scores(session, totals)
            if session.status != PersonalitySessionStatus.COMPLETED:
                # Tugallanmagan sessiyada natija turi ko'rsatilmaydi.
                session.result_type = None
            updated += 1
        self.db.flush()
        return updated

    def delete_stale_visited_sessions(self, *, older_than_days: int) -> int:
        """Hech qachon boshlanmagan (VISITED) eski sessiyalarni o'chiradi.

        O'chirishning O'ZI bu yerda emas: butun mantiq (xavfsizlik shartlari va
        eng muhimi — o'chirishdan oldin kunlik agregatga yig'ish) saqlash siyosati
        xizmatida. Ikkinchi, mustaqil o'chirish yo'li bo'lsa, u agregat qadamini
        o'tkazib yuborib voronka tarixini jimgina yo'q qilardi.

        `older_than_days` KLAMP QILINMAYDI: avval `max(0, ...)` bor edi va 0 (yoki
        manfiy) qiymat kesish chegarasini "hozir" qilib, jadvaldagi BARCHA VISITED
        qatorlarni o'chirib yuborardi — sozlamada "o'chirilgan" deb o'qiladigan qiymat.
        """
        if older_than_days < 1:
            raise ValueError("older_than_days kamida 1 bo'lishi kerak (0 = qoida o'chirilgan)")
        from app.services import retention_service

        report = retention_service.run(
            self.db,
            dry_run=False,
            rules=[retention_service.RULE_VISITED],
            days_override={retention_service.RULE_VISITED: older_than_days},
        )
        self.db.expire_all()
        return report.rules[0].affected

    def update_session_progress(self, session: PersonalityTestSession, index: int) -> None:
        session.current_question_index = index
        session.last_activity_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_result_content(
        self, personality_type: str, language: str = DEFAULT_CONTENT_LANGUAGE
    ) -> PersonalityResultContent | None:
        content = self._result_content(personality_type, language)
        if content is None and language != DEFAULT_CONTENT_LANGUAGE:
            content = self._result_content(personality_type, DEFAULT_CONTENT_LANGUAGE)
        return content

    def _result_content(self, personality_type: str, language: str) -> PersonalityResultContent | None:
        stmt = select(PersonalityResultContent).where(
            PersonalityResultContent.personality_type == personality_type,
            PersonalityResultContent.language == language,
            PersonalityResultContent.is_active.is_(True),
        )
        return self.db.scalar(stmt)

    def set_premium(
        self,
        session_id: int,
        *,
        is_premium: bool = True,
        set_approved_at: bool = True,
    ) -> PersonalityTestSession | None:
        session = self.get_session_by_id(session_id)
        if not session:
            return None
        session.is_premium = is_premium
        if is_premium and set_approved_at:
            session.premium_approved_at = session.premium_approved_at or datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(session)
        return session

    def request_premium(self, session: PersonalityTestSession) -> PersonalityTestSession:
        session.premium_requested = True
        # Vaqt belgisisiz "premium so'raldi" voronkada sanab bo'lmaydigan holat edi.
        session.premium_requested_at = session.premium_requested_at or datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(session)
        return session

    def set_appearance_theme(
        self, session: PersonalityTestSession, theme: AppearanceTheme
    ) -> PersonalityTestSession:
        session.appearance_theme = theme
        self.db.flush()
        self.db.refresh(session)
        return session

    @staticmethod
    def parse_json_list(raw: str) -> list[str]:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data]
        except json.JSONDecodeError:
            pass
        return [line.strip() for line in raw.splitlines() if line.strip()]

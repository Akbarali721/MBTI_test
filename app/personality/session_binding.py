from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.personality.themes import PERSONALITY_SESSION_COOKIE_KEY, has_appearance_choice
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_service import PersonalityService


def get_bound_session(request: Request, db: Session) -> PersonalityTestSession | None:
    token = request.session.get(PERSONALITY_SESSION_COOKIE_KEY)
    if not token:
        return None
    return PersonalityRepository(db).get_session_by_token(token)


def assign_session_cookie(request: Request, session: PersonalityTestSession) -> None:
    request.session[PERSONALITY_SESSION_COOKIE_KEY] = session.token


def _normalize_source(source: str | None) -> str | None:
    if not source:
        return None
    cleaned = source.strip()[:64]
    return cleaned or None


def ensure_visitor_session(
    request: Request,
    db: Session,
    *,
    source: str | None = None,
) -> PersonalityTestSession:
    repo = PersonalityRepository(db)
    normalized_source = _normalize_source(source)
    existing = get_bound_session(request, db)
    if existing:
        if existing.status == PersonalitySessionStatus.COMPLETED:
            session = repo.create_session(source=normalized_source, status=PersonalitySessionStatus.VISITED)
            assign_session_cookie(request, session)
            return session
        if normalized_source and not existing.source:
            repo.set_source_if_empty(existing, normalized_source)
        return existing
    session = repo.create_session(source=normalized_source, status=PersonalitySessionStatus.VISITED)
    assign_session_cookie(request, session)
    return session


def create_fresh_session(
    request: Request,
    db: Session,
    *,
    telegram_user_id: str | None = None,
    copy_gender_from: PersonalityTestSession | None = None,
) -> PersonalityTestSession:
    service = PersonalityService(db)
    session = service.start_session(telegram_user_id=telegram_user_id)
    if copy_gender_from and has_appearance_choice(copy_gender_from):
        theme = copy_gender_from.appearance_theme
        assert theme is not None
        service.set_appearance(session.token, theme)
        session = service.get_session_or_404(session.token)
    assign_session_cookie(request, session)
    return session


def bind_personality_session(
    request: Request,
    db: Session,
    *,
    telegram_user_id: str | None = None,
) -> PersonalityTestSession:
    existing = get_bound_session(request, db)
    if existing:
        if existing.status != PersonalitySessionStatus.COMPLETED:
            return existing
    return create_fresh_session(request, db, telegram_user_id=telegram_user_id)


def redirect_for_session_progress(session: PersonalityTestSession) -> RedirectResponse | None:
    if session.status == PersonalitySessionStatus.COMPLETED:
        return RedirectResponse(url=f"/personality/result/{session.token}", status_code=303)
    if session.current_question_index > 0 or session.status == PersonalitySessionStatus.IN_PROGRESS:
        return RedirectResponse(url=f"/personality/test/{session.token}", status_code=303)
    if session.status == PersonalitySessionStatus.STARTED and (session.answered_questions or 0) > 0:
        return RedirectResponse(url=f"/personality/test/{session.token}", status_code=303)
    return None


def redirect_for_incomplete_result(session: PersonalityTestSession) -> RedirectResponse | None:
    if session.status == PersonalitySessionStatus.COMPLETED:
        return None
    if session.current_question_index > 0 or session.status == PersonalitySessionStatus.IN_PROGRESS:
        q = session.current_question_index
        return RedirectResponse(url=f"/personality/test/{session.token}?q={q}", status_code=303)
    if session.status == PersonalitySessionStatus.STARTED and (session.answered_questions or 0) > 0:
        q = session.current_question_index
        return RedirectResponse(url=f"/personality/test/{session.token}?q={q}", status_code=303)
    return RedirectResponse(url="/personality/instructions", status_code=303)

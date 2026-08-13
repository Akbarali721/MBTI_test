import re
import secrets

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import PersonalitySessionStatus
from app.models.personality import PersonalityTestSession
from app.personality.analytics_constants import DEFAULT_SOURCE
from app.personality.themes import PERSONALITY_SESSION_COOKIE_KEY, has_appearance_choice
from app.repositories.personality_repository import PersonalityRepository
from app.services import referral_service
from app.services.personality_service import PersonalityService

COMPLETED_TOKENS_KEY = "personality_completed_tokens"
PENDING_REFERRAL_KEY = "personality_pending_ref"
PENDING_SOURCE_KEY = "personality_pending_source"
FEEDBACK_SKIPPED_KEY = "personality_feedback_skipped"
MAX_COMPLETED_TOKENS = 5

RESULT_ACCESS_SALT = "personality-result-access"
RESULT_ACCESS_MAX_AGE_SECONDS = 7 * 24 * 60 * 60

# Kraulerlar/monitoringlar landing sahifasida anonim sessiya qatorlarini ko'paytirmasligi uchun.
_NON_HUMAN_UA_RE = re.compile(
    r"bot\b|bot/|crawler|spider|slurp|scrapy|curl/|wget/|python-requests|python-httpx|"
    r"go-http-client|okhttp|libwww|headlesschrome|lighthouse|pingdom|uptimerobot|"
    r"bingpreview|facebookexternalhit",
    re.IGNORECASE,
)
_PREFETCH_HEADERS = (
    ("purpose", "prefetch"),
    ("sec-purpose", "prefetch"),
    ("x-purpose", "preview"),
    ("x-moz", "prefetch"),
)


def is_non_human_request(request: Request) -> bool:
    """Kraulerlar, prefetch va monitoring so'rovlari — ular uchun sessiya qatori yaratilmaydi."""
    user_agent = request.headers.get("user-agent", "").strip()
    if not user_agent or _NON_HUMAN_UA_RE.search(user_agent):
        return True
    return any(marker in request.headers.get(name, "").lower() for name, marker in _PREFETCH_HEADERS)


def get_bound_session(request: Request, db: Session) -> PersonalityTestSession | None:
    token = request.session.get(PERSONALITY_SESSION_COOKIE_KEY)
    if not token:
        return None
    return PersonalityRepository(db).get_session_by_token(token)


def assign_session_cookie(request: Request, session: PersonalityTestSession) -> None:
    request.session[PERSONALITY_SESSION_COOKIE_KEY] = session.token


def completed_tokens(request: Request) -> list[str]:
    raw = request.session.get(COMPLETED_TOKENS_KEY)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def remember_completed_token(request: Request, token: str) -> None:
    """Cookie almashsa ham tugallangan natijaga kirish yo'qolmasligi uchun cheklangan ro'yxat."""
    tokens = [item for item in completed_tokens(request) if item != token]
    tokens.append(token)
    request.session[COMPLETED_TOKENS_KEY] = tokens[-MAX_COMPLETED_TOKENS:]


def _result_access_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt=RESULT_ACCESS_SALT)


def make_result_access_token(token: str) -> str:
    """Natijani boshqa qurilmada ochish uchun 7 kunlik imzolangan token."""
    return _result_access_serializer().dumps(token)


def verify_result_access_token(token: str, signed: str) -> bool:
    if not token or not signed:
        return False
    try:
        payload = _result_access_serializer().loads(signed, max_age=RESULT_ACCESS_MAX_AGE_SECONDS)
    except BadSignature:
        return False
    if not isinstance(payload, str):
        return False
    return secrets.compare_digest(payload.encode("utf-8"), token.encode("utf-8"))


def may_access_session(
    request: Request,
    db: Session,
    token: str,
    *,
    access: str | None = None,
) -> bool:
    bound = get_bound_session(request, db)
    if bound and bound.token == token:
        return True
    if token in completed_tokens(request):
        return True
    if access and verify_result_access_token(token, access):
        # Imzolangan havola bilan kelgan qurilma sahifani qayta yuklay olishi kerak.
        remember_completed_token(request, token)
        return True
    return False


def _normalize_source(source: str | None) -> str | None:
    if not source:
        return None
    cleaned = source.strip()[:64]
    return cleaned or None


def remember_source_code(request: Request, source: str | None) -> None:
    normalized = _normalize_source(source)
    if normalized:
        request.session[PENDING_SOURCE_KEY] = normalized


def pending_source_code(request: Request) -> str | None:
    raw = request.session.get(PENDING_SOURCE_KEY)
    if isinstance(raw, str):
        return _normalize_source(raw)
    return None


def _resolve_source_code(request: Request, source: str | None) -> str | None:
    if source:
        remember_source_code(request, source)
    return _normalize_source(source) or pending_source_code(request)


def sync_source_attribution(
    request: Request,
    db: Session,
    session: PersonalityTestSession,
    source: str | None,
) -> None:
    resolved = _resolve_source_code(request, source)
    if not resolved:
        return
    PersonalityRepository(db).set_source_if_empty(session, resolved)


def session_needs_intent(session: PersonalityTestSession) -> bool:
    """Intent faqat test boshlanishidan oldin, bir marta so'raladi."""
    if session.intent:
        return False
    if session.status == PersonalitySessionStatus.COMPLETED:
        return False
    if (session.answered_questions or 0) > 0:
        return False
    return True


def redirect_for_intent_or_none(session: PersonalityTestSession) -> RedirectResponse | None:
    if not session_needs_intent(session):
        return None
    if not has_appearance_choice(session):
        return None
    return RedirectResponse(url="/personality/intent", status_code=303)


def feedback_skipped_for(request: Request, token: str) -> bool:
    skipped = request.session.get(FEEDBACK_SKIPPED_KEY)
    if isinstance(skipped, list):
        return token in skipped
    return False


def remember_feedback_skipped(request: Request, token: str) -> None:
    skipped = request.session.get(FEEDBACK_SKIPPED_KEY)
    if not isinstance(skipped, list):
        skipped = []
    if token not in skipped:
        skipped.append(token)
    request.session[FEEDBACK_SKIPPED_KEY] = skipped


def remember_referral_code(request: Request, code: str | None) -> None:
    """Taklif kodini brauzer sessiyasida saqlaydi — keyingi sessiya yaratilganda qo'llash uchun."""
    normalized = referral_service.normalize_code(code)
    if normalized:
        request.session[PENDING_REFERRAL_KEY] = normalized


def pending_referral_code(request: Request) -> str | None:
    raw = request.session.get(PENDING_REFERRAL_KEY)
    if isinstance(raw, str):
        return referral_service.normalize_code(raw)
    return None


def clear_pending_referral(request: Request) -> None:
    request.session.pop(PENDING_REFERRAL_KEY, None)


def _resolve_referral_code(request: Request, ref: str | None) -> str | None:
    if ref:
        remember_referral_code(request, ref)
    return referral_service.normalize_code(ref) or pending_referral_code(request)


def sync_referral_attribution(
    request: Request,
    db: Session,
    session: PersonalityTestSession,
    ref: str | None,
) -> None:
    """Taklif havolasini sessiyaga biriktiradi (shartlar `referral_service` da).

    `?ref=` faqat landingda emas — kod Starlette sessiyasida saqlanadi va
    `/begin`, `/instructions` va yangi sessiya yaratilganda qayta qo'llanadi.
    Aks holda `create_fresh_session` referralsiz qator ochib, progress 0/3 da qoladi.
    """
    if session.referred_by_session_id is not None:
        clear_pending_referral(request)
        return
    code = _resolve_referral_code(request, ref)
    if not code:
        return
    referral_service.attribute_session(
        db,
        session=session,
        code=code,
        browser_has_completed_test=bool(completed_tokens(request)),
    )


def ensure_visitor_session(
    request: Request,
    db: Session,
    *,
    source: str | None = None,
    ref: str | None = None,
) -> PersonalityTestSession | None:
    if is_non_human_request(request):
        return None
    repo = PersonalityRepository(db)
    resolved_source = _resolve_source_code(request, source)
    existing = get_bound_session(request, db)
    if existing:
        # Tugallangan sessiya cookie'si bu yerda almashtirilmaydi: aks holda premium natija yo'qoladi.
        sync_source_attribution(request, db, existing, source)
        sync_referral_attribution(request, db, existing, ref)
        return existing
    session = repo.create_session(source=resolved_source, status=PersonalitySessionStatus.VISITED)
    assign_session_cookie(request, session)
    sync_source_attribution(request, db, session, source)
    sync_referral_attribution(request, db, session, ref)
    return session


def create_fresh_session(
    request: Request,
    db: Session,
    *,
    telegram_user_id: int | None = None,
    copy_gender_from: PersonalityTestSession | None = None,
    ref: str | None = None,
    source: str | None = None,
) -> PersonalityTestSession:
    service = PersonalityService(db)
    resolved_source = _resolve_source_code(request, source)
    session = service.start_session(
        telegram_user_id=telegram_user_id,
        source=resolved_source,
    )
    if copy_gender_from is not None:
        if copy_gender_from.source and copy_gender_from.source != DEFAULT_SOURCE:
            PersonalityRepository(db).set_source_if_empty(session, copy_gender_from.source)
        if has_appearance_choice(copy_gender_from):
            theme = copy_gender_from.appearance_theme
            if theme is not None:
                service.set_appearance(session.token, theme)
                session = service.get_session_or_404(session.token)
    assign_session_cookie(request, session)
    sync_source_attribution(request, db, session, source)
    sync_referral_attribution(request, db, session, ref)
    return session


def start_new_test(request: Request, db: Session) -> PersonalityTestSession:
    """«Testni qayta ishlash» — yangi sessiya yaratiladigan yagona joy."""
    previous = get_bound_session(request, db)
    if previous is not None and previous.status == PersonalitySessionStatus.COMPLETED:
        remember_completed_token(request, previous.token)
    return create_fresh_session(request, db, copy_gender_from=previous)


def bind_personality_session(
    request: Request,
    db: Session,
    *,
    telegram_user_id: int | None = None,
    ref: str | None = None,
    source: str | None = None,
) -> PersonalityTestSession:
    existing = get_bound_session(request, db)
    if existing:
        sync_source_attribution(request, db, existing, source)
        sync_referral_attribution(request, db, existing, ref)
        return existing
    return create_fresh_session(
        request,
        db,
        telegram_user_id=telegram_user_id,
        ref=ref,
        source=source,
    )


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

import logging

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db_session
from app.i18n import resolve_lang
from app.models.enums import AppearanceTheme
from app.personality.payment_code import payment_code_for_session
from app.personality.session_binding import (
    bind_personality_session,
    ensure_visitor_session,
    get_bound_session,
    may_access_session,
    redirect_for_incomplete_result,
    redirect_for_session_progress,
    start_new_test,
)
from app.personality.themes import (
    SELECTABLE_APPEARANCE_VALUES,
    has_appearance_choice,
    theme_template_context,
)
from app.services.personality_service import PersonalityService
from app.services.premium_payment_service import (
    PremiumPaymentService,
    format_price_uzs,
    premium_deeplink_url,
    support_bot_public_url,
)
from app.templating import templates

router = APIRouter(prefix="/personality", tags=["personality"])
logger = logging.getLogger(__name__)

PRODUCT_NAME = "Xarakteringiz va sizga mos hayot uslubini aniqlash testi"

ALLOWED_APPEARANCE_VALUES = SELECTABLE_APPEARANCE_VALUES


def _themed_context(session) -> dict:
    return theme_template_context(session)


def _require_session_owner(
    request: Request,
    token: str,
    db: Session,
    access: str | None = None,
) -> RedirectResponse | None:
    if may_access_session(request, db, token, access=access):
        return None
    return RedirectResponse(url="/personality", status_code=303)


@router.get("", response_class=HTMLResponse)
def personality_landing(
    request: Request,
    db: Session = Depends(get_db_session),
    source: str | None = Query(default=None),
) -> HTMLResponse:
    ensure_visitor_session(request, db, source=source)
    return templates.TemplateResponse(
        request,
        "personality/landing.html",
        {"product_name": PRODUCT_NAME},
    )


@router.post("/begin")
def personality_begin(
    request: Request,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    bind_personality_session(request, db)
    return RedirectResponse(url="/personality/instructions", status_code=303)


@router.post("/restart")
def personality_restart(
    request: Request,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    start_new_test(request, db)
    return RedirectResponse(url="/personality/instructions", status_code=303)


@router.get("/appearance", response_class=HTMLResponse, response_model=None)
def personality_appearance_get(
    request: Request,
    db: Session = Depends(get_db_session),
    telegram_user_id: int | None = Query(default=None),
) -> RedirectResponse:
    bind_personality_session(request, db, telegram_user_id=telegram_user_id)
    return RedirectResponse(url="/personality/instructions", status_code=303)


@router.post("/appearance", response_model=None)
def personality_appearance_post(
    request: Request,
    db: Session = Depends(get_db_session),
    appearance_theme: str = Form(...),
) -> RedirectResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db)

    if appearance_theme in ALLOWED_APPEARANCE_VALUES:
        theme = AppearanceTheme(appearance_theme)
        PersonalityService(db).set_appearance(session.token, theme)
    return RedirectResponse(url="/personality/instructions", status_code=303)


def _instructions_context(session, *, gender_error: str | None = None) -> dict:
    ctx = _themed_context(session)
    theme = session.appearance_theme if has_appearance_choice(session) else None
    ctx["selected_gender"] = theme.value if theme else None
    ctx["gender_error"] = gender_error
    return ctx


@router.get("/instructions", response_class=HTMLResponse, response_model=None)
def personality_instructions(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db)

    advanced = redirect_for_session_progress(session)
    if advanced:
        return advanced

    return templates.TemplateResponse(
        request,
        "personality/instructions.html",
        _instructions_context(session),
    )


@router.post("/start", response_model=None)
def personality_start(
    request: Request,
    db: Session = Depends(get_db_session),
    telegram_user_id: int | None = Query(default=None),
    gender: str | None = Form(default=None),
) -> RedirectResponse | HTMLResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db, telegram_user_id=telegram_user_id)

    if not gender or gender not in ALLOWED_APPEARANCE_VALUES:
        return templates.TemplateResponse(
            request,
            "personality/instructions.html",
            _instructions_context(
                session,
                gender_error="Davom etish uchun jinsingizni tanlang.",
            ),
            status_code=400,
        )

    theme = AppearanceTheme(gender)
    PersonalityService(db).set_appearance(session.token, theme)
    return RedirectResponse(url=f"/personality/test/{session.token}", status_code=303)


def _require_appearance_or_redirect(session) -> RedirectResponse | None:
    if not has_appearance_choice(session):
        return RedirectResponse(url="/personality/instructions", status_code=303)
    return None


@router.get("/test/{token}", response_class=HTMLResponse, response_model=None)
def personality_test(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    q: int | None = Query(default=None, ge=0),
) -> HTMLResponse | RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    service = PersonalityService(db)
    view = service.get_test_view(token, question_index=q)
    if view.get("redirect") == "result":
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    if view.get("redirect") == "questions_error":
        return templates.TemplateResponse(request, "personality/questions_error.html", {})

    session = view["session"]
    appearance_redirect = _require_appearance_or_redirect(session)
    if appearance_redirect:
        return appearance_redirect
    ctx = _themed_context(session)
    ctx.update(
        {
            "token": token,
            "session": session,
            "question": view["question"],
            "question_index": view["question_index"],
            "progress_display": view["progress_display"],
            "total": view["total"],
            "selected_option_id": view["selected_option_id"],
        }
    )
    logger.info(
        "personality question page session_id=%s question_index=%s theme=%s",
        session.id,
        view["question_index"],
        getattr(session.appearance_theme, "value", session.appearance_theme),
    )
    return templates.TemplateResponse(request, "personality/question.html", ctx)


@router.post("/test/{token}/answer", response_model=None)
def personality_answer(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    question_id: int = Form(...),
    option_id: int = Form(...),
    question_index: int = Form(...),
) -> RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    service = PersonalityService(db)
    outcome = service.submit_answer(
        token,
        question_id=question_id,
        option_id=option_id,
        question_index=question_index,
    )
    if outcome["redirect"] == "loading":
        return RedirectResponse(url=f"/personality/result/{token}/loading", status_code=303)
    if outcome["redirect"] == "result":
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    next_index = outcome["next_index"]
    return RedirectResponse(url=f"/personality/test/{token}?q={next_index}", status_code=303)


@router.get("/result/{token}/loading", response_class=HTMLResponse, response_model=None)
def personality_loading(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    service = PersonalityService(db)
    session = service.get_session_or_404(token)
    appearance_redirect = _require_appearance_or_redirect(session)
    if appearance_redirect:
        return appearance_redirect
    ctx = _themed_context(session)
    ctx["token"] = token
    return templates.TemplateResponse(request, "personality/loading.html", ctx)


@router.get("/result/{token}", response_class=HTMLResponse, response_model=None)
def personality_result(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    access: str | None = Query(default=None),
) -> HTMLResponse | RedirectResponse:
    denied = _require_session_owner(request, token, db, access=access)
    if denied:
        return denied
    service = PersonalityService(db)
    session = service.get_session_or_404(token)
    incomplete = redirect_for_incomplete_result(session)
    if incomplete:
        return incomplete

    # Kontent tili interfeys tili bilan bir xil bo'lishi kerak; yozuv topilmasa repozitoriy "uz" ga qaytadi.
    view = service.get_result_view(token, language=resolve_lang(request))
    session = view["session"]
    appearance_redirect = _require_appearance_or_redirect(session)
    if appearance_redirect:
        return appearance_redirect
    content = view["content"]
    result = view["result"]
    payment_status = PremiumPaymentService(db).get_result_payment_status(session)
    payment_code = payment_code_for_session(db, session)
    support_bot_url = support_bot_public_url()
    deeplink_url = premium_deeplink_url(token)
    ctx = _themed_context(session)
    ctx.update(
        {
            "token": token,
            "session": session,
            "content": content,
            "result": result,
            "strengths": view["strengths"],
            "challenges": view["challenges"],
            "is_premium": session.is_premium,
            "payment_status": payment_status,
            "premium_price": settings.premium_price,
            "premium_price_display": format_price_uzs(settings.premium_price),
            "payment_card_number": settings.payment_card_number,
            "payment_card_holder": settings.payment_card_holder,
            "payment_support_configured": bool(deeplink_url or support_bot_url),
            "payment_support_bot_url": support_bot_url or "",
            "payment_code": payment_code,
            "result_page_url": f"/personality/result/{token}",
            "premium_deeplink_url": deeplink_url,
            # Deep link sozlanmagan holat uchun zaxira: server tomonda yo'naltiradi.
            "support_bot_open_url": f"/personality/result/{token}/support-bot",
        }
    )
    return templates.TemplateResponse(request, "personality/result.html", ctx)


def _support_bot_redirect_url(token: str) -> str:
    return premium_deeplink_url(token) or support_bot_public_url() or f"/personality/result/{token}"


@router.get("/result/{token}/support-bot", response_model=None)
def personality_support_bot(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    """GET faqat yo'naltiradi — to'lov yozuvi POST orqali yaratiladi."""
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    return RedirectResponse(url=_support_bot_redirect_url(token), status_code=303)


@router.post("/result/{token}/support-bot", response_model=None)
def personality_support_bot_start(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    PremiumPaymentService(db).begin_web_manual_payment(token)
    return RedirectResponse(url=_support_bot_redirect_url(token), status_code=303)


@router.post("/result/{token}/payment-telegram", response_model=None)
def personality_payment_telegram_legacy(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    """Legacy POST — redirects to support-bot flow."""
    return personality_support_bot_start(request, token, db)


@router.post("/result/{token}/request-premium", response_model=None)
def personality_request_premium(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    PersonalityService(db).request_premium_access(token)
    return RedirectResponse(url=f"/personality/result/{token}?premium_requested=1", status_code=303)

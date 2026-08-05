import logging

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db_session
from app.models.enums import AppearanceTheme
from app.personality.session_binding import (
    bind_personality_session,
    create_fresh_session,
    ensure_visitor_session,
    get_bound_session,
    redirect_for_incomplete_result,
    redirect_for_session_progress,
)
from app.personality.themes import has_appearance_choice, theme_template_context
from app.services.personality_service import PersonalityService
from app.personality.payment_code import payment_code_for_session
from app.services.premium_payment_service import (
    PremiumPaymentService,
    format_price_uzs,
    support_bot_public_url,
)
from app.templating import templates

router = APIRouter(prefix="/personality", tags=["personality"])
logger = logging.getLogger(__name__)

PRODUCT_NAME = "Xarakteringiz va sizga mos hayot uslubini aniqlash testi"

APPEARANCE_OPTIONS = [
    {
        "value": "male",
        "title": "Erkak",
        "subtitle": "Sokin ko‘k va to‘q ranglar",
        "illustration": "images/personality_male.svg",
    },
    {
        "value": "female",
        "title": "Ayol",
        "subtitle": "Yumshoq binafsha va pastel ranglar",
        "illustration": "images/personality_female.svg",
    },
]

ALLOWED_APPEARANCE_VALUES = frozenset({"male", "female"})


def _appearance_page_context(
    *,
    appearance_error: str | None = None,
    selected_theme: str | None = None,
) -> dict:
    return {
        "appearance_options": APPEARANCE_OPTIONS,
        "appearance_error": appearance_error,
        "selected_theme": selected_theme,
    }


def _themed_context(session) -> dict:
    return theme_template_context(session)


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
    previous = get_bound_session(request, db)
    create_fresh_session(request, db, copy_gender_from=previous)
    return RedirectResponse(url="/personality/instructions", status_code=303)


@router.get("/appearance", response_class=HTMLResponse, response_model=None)
def personality_appearance_get(
    request: Request,
    db: Session = Depends(get_db_session),
    telegram_user_id: str | None = Query(default=None),
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
        bind_personality_session(request, db)
        session = get_bound_session(request, db)
    assert session is not None

    if appearance_theme in ALLOWED_APPEARANCE_VALUES:
        theme = AppearanceTheme(appearance_theme)
        PersonalityService(db).set_appearance(session.token, theme)
    return RedirectResponse(url="/personality/instructions", status_code=303)


def _instructions_context(session, *, gender_error: str | None = None) -> dict:
    ctx = _themed_context(session)
    selected = None
    if has_appearance_choice(session):
        selected = session.appearance_theme.value  # type: ignore[union-attr]
    ctx["selected_gender"] = selected
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
    telegram_user_id: str | None = Query(default=None),
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
        "personality question page token=%s gender=%s theme_class=%s appearance_theme=%s",
        token,
        ctx.get("gender"),
        ctx.get("theme_class"),
        getattr(session.appearance_theme, "value", session.appearance_theme),
    )
    return templates.TemplateResponse(request, "personality/question.html", ctx)


@router.post("/test/{token}/answer")
def personality_answer(
    token: str,
    db: Session = Depends(get_db_session),
    question_id: int = Form(...),
    option_id: int = Form(...),
    question_index: int = Form(...),
) -> RedirectResponse:
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


def _require_session_owner(request: Request, token: str, db: Session):
    bound = get_bound_session(request, db)
    if not bound or bound.token != token:
        return RedirectResponse(url="/personality", status_code=303)
    return None


@router.get("/result/{token}", response_class=HTMLResponse, response_model=None)
def personality_result(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    service = PersonalityService(db)
    session = service.get_session_or_404(token)
    incomplete = redirect_for_incomplete_result(session)
    if incomplete:
        return incomplete

    view = service.get_result_view(token)
    session = view["session"]
    appearance_redirect = _require_appearance_or_redirect(session)
    if appearance_redirect:
        return appearance_redirect
    content = view["content"]
    result = view["result"]
    payment_service = PremiumPaymentService(db)
    payment_status = payment_service.get_result_payment_status(session)
    payment_code = payment_code_for_session(db, session)
    support_bot_url = support_bot_public_url()
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
            "payment_support_configured": support_bot_url is not None,
            "payment_support_bot_url": support_bot_url or "",
            "payment_code": payment_code,
            "result_page_url": f"/personality/result/{token}",
            "support_bot_open_url": f"/personality/result/{token}/support-bot",
        }
    )
    return templates.TemplateResponse(request, "personality/result.html", ctx)


@router.get("/result/{token}/support-bot", response_model=None)
def personality_support_bot(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    PremiumPaymentService(db).begin_web_manual_payment(token)
    url = support_bot_public_url()
    if not url:
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    return RedirectResponse(url=url, status_code=303)


@router.post("/result/{token}/payment-telegram")
def personality_payment_telegram_legacy(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    """Legacy POST — redirects to support-bot flow."""
    return personality_support_bot(request, token, db)


@router.post("/result/{token}/request-premium")
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

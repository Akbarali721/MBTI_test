import logging

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.config import settings
from app.dependencies import get_db_session
from app.i18n import resolve_lang
from app.models.enums import AppearanceTheme, PersonalitySessionStatus
from app.pdf import pdf_filename
from app.personality.payment_code import payment_code_for_session
from app.personality.analytics_constants import (
    FEEDBACK_INTEREST_VALUES,
    FEEDBACK_RATING_VALUES,
    INTENT_VALUES,
)
from app.personality.session_binding import (
    bind_personality_session,
    clear_pending_referral,
    completed_tokens,
    ensure_visitor_session,
    feedback_skipped_for,
    get_bound_session,
    may_access_session,
    redirect_for_incomplete_result,
    redirect_for_intent_or_none,
    redirect_for_session_progress,
    remember_feedback_skipped,
    remember_referral_code,
    remember_source_code,
    session_needs_intent,
    start_new_test,
    sync_referral_attribution,
    sync_source_attribution,
)
from app.personality.share_code import share_code_for_session, share_path, telegram_share_url
from app.personality.themes import (
    SELECTABLE_APPEARANCE_VALUES,
    has_appearance_choice,
    theme_template_context,
)
from app.ratelimit import limiter as advice_limiter
from app.repositories.personality_repository import PersonalityRepository
from app.services import ai_advice_service, referral_service
from app.services.personality_scoring import calculate_personality_result
from app.services.personality_service import PersonalityService
from app.services.premium_access import has_premium_access, trial_days_left
from app.services.premium_payment_service import (
    PremiumPaymentService,
    format_price_uzs,
    premium_deeplink_url,
    support_bot_public_url,
)
from app.services.premium_presentation import compose_premium_blocks
from app.services.result_pdf import PdfFontsUnavailable, PdfNotPremium, build_pdf_bytes
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


def _history_tokens(request: Request, current_token: str | None = None) -> list[str]:
    """Shu brauzer egalik qiladigan tugallangan sessiyalar — eng yangisi oxirida."""
    tokens = [item for item in completed_tokens(request) if item != current_token]
    if current_token:
        tokens.append(current_token)
    return tokens


def _result_title(repo: PersonalityRepository, result_type: str | None, lang: str) -> str:
    if not result_type:
        return ""
    content = repo.get_result_content(result_type, lang)
    return content.title if content else result_type


# left_percent har doim shu qutbga tegishli (yorliqlar dominantlikka qarab almashmaydi),
# shuning uchun urinishlarni to'g'ridan-to'g'ri solishtirish mumkin.
_DIMENSION_POLES = (("ei", "i", "e"), ("sn", "s", "n"), ("tf", "t", "f"), ("jp", "j", "p"))


def _dimension_shifts(entries: list[dict]) -> list[dict]:
    """Birinchi va oxirgi urinish orasidagi farq — takror topshirishning asosiy qiymati."""
    if len(entries) < 2:
        return []
    first, last = entries[0]["result"], entries[-1]["result"]
    return [
        {
            "left_key": left_key,
            "right_key": right_key,
            "before": getattr(first, name).left_percent,
            "after": getattr(last, name).left_percent,
            "delta": getattr(last, name).left_percent - getattr(first, name).left_percent,
        }
        for name, left_key, right_key in _DIMENSION_POLES
    ]


@router.get("", response_class=HTMLResponse)
def personality_landing(
    request: Request,
    db: Session = Depends(get_db_session),
    source: str | None = Query(default=None),
    # `max_length` ATAYLAB yo'q: buzilgan yoki kesilgan havola 422 xato sahifasini
    # emas, oddiy landingni ko'rsatishi kerak. Kod `normalize_code` da tekshiriladi.
    ref: str | None = Query(default=None),
) -> HTMLResponse:
    ensure_visitor_session(request, db, source=source, ref=ref)
    return templates.TemplateResponse(
        request,
        "personality/landing.html",
        {"product_name": PRODUCT_NAME},
    )


@router.get("/history", response_class=HTMLResponse, response_model=None)
def personality_history(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """Shu brauzerda tugallangan testlar va o'lchovlarning vaqt bo'yicha o'zgarishi."""
    bound = get_bound_session(request, db)
    current_token = bound.token if bound and bound.status == PersonalitySessionStatus.COMPLETED else None
    tokens = _history_tokens(request, current_token)

    repo = PersonalityRepository(db)
    sessions = repo.get_completed_sessions_by_tokens(tokens)
    lang = resolve_lang(request)
    entries = [
        {
            "token": session.token,
            "result_type": session.result_type,
            "title": _result_title(repo, session.result_type, lang),
            "completed_at": session.completed_at,
            "is_premium": has_premium_access(session),
            "result": calculate_personality_result(
                session.e_score,
                session.i_score,
                session.s_score,
                session.n_score,
                session.t_score,
                session.f_score,
                session.j_score,
                session.p_score,
            ),
        }
        for session in sessions
    ]
    return templates.TemplateResponse(
        request,
        "personality/history.html",
        {"entries": list(reversed(entries)), "shifts": _dimension_shifts(entries)},
    )


@router.post("/telegram-bind", response_model=None)
def personality_telegram_bind(
    request: Request,
    db: Session = Depends(get_db_session),
    init_data: str = Form(..., alias="init_data"),
) -> Response:
    """Telegram WebApp initData orqali sessiyani foydalanuvchiga bog'laydi."""
    from starlette.responses import JSONResponse

    from app.services.telegram_session_bind import bind_session_from_webapp_init_data

    session = get_bound_session(request, db)
    if session is None:
        return JSONResponse({"ok": False, "reason": "no_session"}, status_code=400)
    updated = bind_session_from_webapp_init_data(db, session, init_data)
    if updated is None:
        return JSONResponse({"ok": False, "reason": "invalid_init_data"}, status_code=400)
    db.commit()
    return JSONResponse({"ok": True})


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
) -> RedirectResponse:
    bind_personality_session(request, db)
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
    ref: str | None = Query(default=None),
    source: str | None = Query(default=None),
) -> HTMLResponse | RedirectResponse:
    if ref:
        remember_referral_code(request, ref)
    if source:
        remember_source_code(request, source)
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db, ref=ref, source=source)
    else:
        sync_referral_attribution(request, db, session, ref)
        sync_source_attribution(request, db, session, source)

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
    gender: str | None = Form(default=None),
) -> RedirectResponse | HTMLResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db)

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
    service = PersonalityService(db)
    session = service.prepare_test_start(session, theme)
    db.commit()
    return RedirectResponse(url="/personality/intent", status_code=303)


@router.get("/intent", response_class=HTMLResponse, response_model=None)
def personality_intent_get(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db)

    advanced = redirect_for_session_progress(session)
    if advanced:
        return advanced

    if not has_appearance_choice(session):
        return RedirectResponse(url="/personality/instructions", status_code=303)

    if not session_needs_intent(session):
        return RedirectResponse(url=f"/personality/test/{session.token}?q=0", status_code=303)

    ctx = _themed_context(session)
    ctx["intent_options"] = [
        ("strengths", "intent.option.strengths"),
        ("career", "intent.option.career"),
        ("self_understanding", "intent.option.self_understanding"),
        ("curiosity", "intent.option.curiosity"),
    ]
    return templates.TemplateResponse(request, "personality/intent.html", ctx)


@router.post("/intent", response_model=None)
def personality_intent_post(
    request: Request,
    db: Session = Depends(get_db_session),
    intent: str = Form(...),
) -> RedirectResponse | HTMLResponse:
    session = get_bound_session(request, db)
    if not session:
        session = bind_personality_session(request, db)

    if not has_appearance_choice(session):
        return RedirectResponse(url="/personality/instructions", status_code=303)

    if intent not in INTENT_VALUES:
        ctx = _themed_context(session)
        ctx["intent_options"] = [
            ("strengths", "intent.option.strengths"),
            ("career", "intent.option.career"),
            ("self_understanding", "intent.option.self_understanding"),
            ("curiosity", "intent.option.curiosity"),
        ]
        ctx["intent_error"] = True
        return templates.TemplateResponse(request, "personality/intent.html", ctx, status_code=400)

    PersonalityRepository(db).set_intent(session, intent)
    db.commit()
    return RedirectResponse(url=f"/personality/test/{session.token}?q=0", status_code=303)


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
    session = service.get_session_or_404(token)
    appearance_redirect = _require_appearance_or_redirect(session)
    if appearance_redirect:
        return appearance_redirect
    intent_redirect = redirect_for_intent_or_none(session)
    if intent_redirect:
        return intent_redirect
    PersonalityRepository(db).mark_test_started_if_needed(session)
    db.commit()
    db.refresh(session)
    view = service.get_test_view(token, question_index=q)
    if view.get("redirect") == "result":
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    if view.get("redirect") == "questions_error":
        return templates.TemplateResponse(request, "personality/questions_error.html", {})

    session = view["session"]
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
        session = outcome["session"]
        if session.referred_by_session_id is not None:
            clear_pending_referral(request)
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


def _referral_context(db: Session, session, share_code: str, base_url: str) -> dict | None:
    """Natija sahifasidagi "do'st taklif qiling" bloki.

    Havola shu sahifaning O'ZIDAGI base_url dan quriladi (PUBLIC_BASE_URL dan emas):
    aks holda lokal yoki eski domenda ochilgan sahifa ishlamaydigan havola berardi.
    """
    if not settings.referral_enabled:
        return None
    progress = referral_service.progress(db, session, code=share_code)
    return {
        "url": f"{base_url}/personality?{referral_service.REFERRAL_QUERY_KEY}={share_code}",
        "progress": progress,
        "reward_days": settings.referral_reward_days,
    }


# Foydalanuvchiga ko'rsatiladigan xabar kaliti. Xizmat kodini to'g'ridan-to'g'ri
# chiqarmaymiz: shablon faqat shu ro'yxatdagi kalitlarni biladi.
_ADVICE_NOTICES = {
    ai_advice_service.READY: "ai.notice_ready",
    ai_advice_service.ALREADY: "ai.notice_ready",
    ai_advice_service.DAILY_LIMIT: "ai.notice_busy",
    ai_advice_service.TEMPORARY_ERROR: "ai.notice_retry",
    ai_advice_service.INVALID_RESPONSE: "ai.notice_retry",
    ai_advice_service.PERMANENT_ERROR: "ai.notice_unavailable",
    ai_advice_service.ATTEMPTS_EXHAUSTED: "ai.notice_unavailable",
}


def _advice_notice(code: str | None) -> str | None:
    return _ADVICE_NOTICES.get(code or "")


@router.get("/result/{token}", response_class=HTMLResponse, response_model=None)
def personality_result(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    access: str | None = Query(default=None),
    # Bu yerda ham `max_length` yo'q: noma'lum qiymat `_advice_notice` da None
    # bo'ladi, 422 esa premium natijani butunlay yopib qo'yardi.
    notice: str | None = Query(default=None),
) -> HTMLResponse | RedirectResponse:
    denied = _require_session_owner(request, token, db, access=access)
    if denied:
        return denied
    service = PersonalityService(db)
    session = service.get_session_or_404(token)
    db.refresh(session)
    incomplete = redirect_for_incomplete_result(session)
    if incomplete:
        return incomplete

    # Kontent tili interfeys tili bilan bir xil bo'lishi kerak; yozuv topilmasa repozitoriy "uz" ga qaytadi.
    lang = resolve_lang(request)
    view = service.get_result_view(token, language=lang)
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
    share_code = share_code_for_session(db, session)
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}{share_path(share_code)}"
    ctx = _themed_context(session)
    ctx.update(
        {
            "token": token,
            "share_url": share_url,
            "share_telegram_url": telegram_share_url(share_url, content.title),
            "history_count": len(_history_tokens(request, token)),
            "session": session,
            "content": content,
            "result": result,
            "strengths": view["strengths"],
            "challenges": view["challenges"],
            # Premium bo'limlar TO'LOV yoki MUKOFOT bilan ochiladi; PDF esa faqat
            # to'lov bilan — yuklab olingan fayl sinov muddatidan keyin ham qoladi.
            "is_premium": has_premium_access(session),
            "is_paid_premium": session.is_premium,
            "trial_days_left": trial_days_left(session),
            "referral": _referral_context(db, session, share_code, base_url),
            "advice": ai_advice_service.advice_state(db, session, lang),
            "advice_notice": _advice_notice(notice),
            "ai_advice_count": settings.ai_advice_count,
            "advice_action_url": f"/personality/result/{token}/ai-advice",
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
            "premium_blocks": compose_premium_blocks(
                content,
                view["strengths"],
                view["challenges"],
                language=lang,
            ),
            "feedback_skipped": feedback_skipped_for(request, token),
            "show_feedback_rating": (
                not feedback_skipped_for(request, token) and not session.feedback_rating
            ),
            "show_feedback_interest": (
                not feedback_skipped_for(request, token)
                and bool(session.feedback_rating)
                and not session.feedback_interest
            ),
            "feedback_rating_options": [
                ("very_accurate", "feedback.rating.very_accurate"),
                ("partly_accurate", "feedback.rating.partly_accurate"),
                ("not_accurate", "feedback.rating.not_accurate"),
            ],
            "feedback_interest_options": [
                ("career", "feedback.interest.career"),
                ("strengths", "feedback.interest.strengths"),
                ("relationships", "feedback.interest.relationships"),
                ("stress", "feedback.interest.stress"),
                ("confidence", "feedback.interest.confidence"),
            ],
        }
    )
    return templates.TemplateResponse(request, "personality/result.html", ctx)


@router.post("/result/{token}/feedback", response_model=None)
def personality_result_feedback(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    rating: str | None = Form(default=None),
    interest: str | None = Form(default=None),
    skip: str | None = Form(default=None),
) -> RedirectResponse:
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    session = PersonalityService(db).get_session_or_404(token)
    if session.status != PersonalitySessionStatus.COMPLETED:
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)

    repo = PersonalityRepository(db)
    if skip:
        remember_feedback_skipped(request, token)
        db.commit()
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)

    if rating and rating in FEEDBACK_RATING_VALUES:
        repo.set_feedback_rating(session, rating)
        db.commit()
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)

    if interest and interest in FEEDBACK_INTEREST_VALUES:
        repo.set_feedback_interest(session, interest)
        db.commit()
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)

    return RedirectResponse(url=f"/personality/result/{token}", status_code=303)


@router.get("/result/{token}/pdf", response_model=None)
def personality_result_pdf(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
    access: str | None = Query(default=None),
) -> Response:
    """Premium natijaning PDF nusxasi — faqat egasi va faqat to'lov tasdiqlangach."""
    denied = _require_session_owner(request, token, db, access=access)
    if denied:
        return denied
    session = PersonalityService(db).get_session_or_404(token)
    if not session.is_premium:
        # Pullik kontent PDF orqali chetlab o'tilmasligi kerak.
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)

    try:
        payload = build_pdf_bytes(db, token, lang=resolve_lang(request), base_url=str(request.base_url))
    except PdfNotPremium:
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    except PdfFontsUnavailable:
        logger.error("PDF yaratilmadi: shriftlar topilmadi (scripts/fetch_pdf_fonts.py)")
        raise StarletteHTTPException(status_code=503) from None

    filename = pdf_filename(session.result_type or "natija")
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/result/{token}/ai-advice", response_model=None)
@advice_limiter.limit(settings.rate_limit_ai_advice)
def personality_ai_advice(
    request: Request,
    token: str,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    """5 ta AI maslahatni yaratadi.

    Alohida POST, sahifa render qilishning ichida emas: tashqi chaqiruv soniyalab
    davom etadi va natija sahifasi undan mustaqil ochilishi kerak. Javob kodi
    manzilga qo'yiladi, ya'ni sahifani yangilash qayta so'rov yubormaydi.
    """
    denied = _require_session_owner(request, token, db)
    if denied:
        return denied
    session = PersonalityService(db).get_session_or_404(token)
    code = ai_advice_service.generate(db, session, language=resolve_lang(request))
    if code in (ai_advice_service.DISABLED, ai_advice_service.NOT_PREMIUM):
        # Funksiya o'chiq yoki premium yo'q: sahifa buni o'zi ko'rsatadi.
        return RedirectResponse(url=f"/personality/result/{token}", status_code=303)
    return RedirectResponse(url=f"/personality/result/{token}?notice={code}#ai-advice", status_code=303)


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

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, verify_admin_credentials
from app.repositories.payment_repository import PaymentRepository
from app.services.admin_analytics_service import AdminAnalyticsService
from app.services.personality_service import PersonalityService
from app.services.premium_payment_service import PremiumPaymentService
from app.templating import templates


def _admin_redirect(request: Request) -> RedirectResponse | None:
    if request.session.get("admin_authenticated") is not True:
        return RedirectResponse(url="/admin/login", status_code=303)
    return None


router = APIRouter(prefix="/admin", tags=["admin"])

STATUS_BADGE = {
    "visited": "secondary",
    "started": "info",
    "in_progress": "warning",
    "completed": "success",
}


@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": None},
    )


@router.post("/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_admin_credentials(username, password):
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"error": "Login yoki parol noto‘g‘ri"},
            status_code=401,
        )
    request.session["admin_authenticated"] = True
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/logout")
def admin_logout(request: Request) -> RedirectResponse:
    request.session.pop("admin_authenticated", None)
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("", response_class=HTMLResponse, response_model=None)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    stats = AdminAnalyticsService(db).dashboard_stats()
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"stats": stats},
    )


@router.get("/sessions", response_class=HTMLResponse, response_model=None)
def admin_sessions_list(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = "all",
    code: str | None = Query(default=None),
) -> HTMLResponse | RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    service = AdminAnalyticsService(db)
    sessions = service.list_sessions(status_filter=filter, payment_code=code)
    from app.personality.payment_code import payment_code_for_session

    session_codes = {s.id: payment_code_for_session(db, s) for s in sessions}
    return templates.TemplateResponse(
        request,
        "admin/sessions.html",
        {
            "sessions": sessions,
            "session_codes": session_codes,
            "current_filter": filter,
            "status_badge": STATUS_BADGE,
            "search_code": (code or "").strip(),
        },
    )


@router.get("/sessions/{session_id}", response_class=HTMLResponse, response_model=None)
def admin_session_detail(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    detail = AdminAnalyticsService(db).get_session_detail(session_id)
    if not detail:
        return RedirectResponse(url="/admin/sessions", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/session_detail.html",
        {
            "session": detail["session"],
            "answers": detail["answers"],
            "status_badge": STATUS_BADGE,
        },
    )


@router.get("/personality/sessions", response_model=None)
def admin_personality_sessions_legacy(request: Request) -> RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    return RedirectResponse(url="/admin/sessions", status_code=303)


@router.post("/personality/{session_id}/grant-premium")
def admin_grant_premium(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    PersonalityService(db).grant_premium(session_id)
    return RedirectResponse(url=f"/admin/sessions/{session_id}", status_code=303)


@router.get("/premium-requests", response_class=HTMLResponse, response_model=None)
def admin_premium_requests(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = "all",
) -> HTMLResponse | RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    payments = PaymentRepository(db).list_for_admin(status_filter=filter)
    return templates.TemplateResponse(
        request,
        "admin/premium_requests.html",
        {"payments": payments, "current_filter": filter},
    )


@router.post("/premium-requests/{payment_id}/approve")
def admin_premium_approve(
    request: Request,
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    PremiumPaymentService(db).approve_payment(payment_id, approved_by="web-admin")
    return RedirectResponse(url="/admin/premium-requests", status_code=303)


@router.post("/premium-requests/{payment_id}/reject")
def admin_premium_reject(
    request: Request,
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    redirect = _admin_redirect(request)
    if redirect:
        return redirect
    PremiumPaymentService(db).reject_payment(payment_id, approved_by="web-admin")
    return RedirectResponse(url="/admin/premium-requests", status_code=303)

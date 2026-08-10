import json
import logging
import mimetypes
from collections.abc import Iterator
from http.client import HTTPResponse
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import urlopen

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.authz import (
    EXPORT_DATA,
    MANAGE_USERS,
    MODERATE_PAYMENTS,
    VIEW_AGGREGATE,
    VIEW_AUDIT,
    VIEW_OPS,
    VIEW_PII,
    AdminIdentity,
    requires,
    role_label,
)
from app.config import settings
from app.dependencies import (
    current_admin,
    get_db_session,
    require_admin,
    start_admin_session,
    verify_admin_credentials,
)
from app.models.enums import AdminRole
from app.models.notification import OUTBOX_WORKER_HEARTBEAT, RETENTION_HEARTBEAT
from app.personality.payment_code import find_sessions_by_payment_code, payment_code_for_session
from app.ratelimit import limiter
from app.repositories.admin_repository import AdminRepository
from app.repositories.payment_repository import PaymentRepository
from app.services import admin_service, audit_service, csv_export, notification_outbox, retention_service
from app.services.admin_analytics_service import (
    DEFAULT_PAGE_SIZE,
    AdminAnalyticsService,
    Page,
    normalize_page,
)
from app.services.premium_payment_service import PremiumPaymentService, format_price_uzs
from app.services.premium_telegram_delivery import try_deliver_premium_approved_message
from app.templating import templates
from app.timeutils import utcnow

logger = logging.getLogger(__name__)

# Autentifikatsiyasiz ochiq qoladigan yagona marshrutlar.
public_router = APIRouter(prefix="/admin", tags=["admin"])
# Qolgan hamma narsa: himoya router darajasida, shuning uchun yangi endpoint
# qo'shilganda uni himoyalashni unutib bo'lmaydi.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

# Chegaralagich butun ilova uchun bitta (app/ratelimit.py). Bu yerdagi nom eski
# import yo'llari uchun saqlanadi.
login_limiter = limiter

STATUS_BADGE = {
    "visited": "secondary",
    "started": "info",
    "in_progress": "warning",
    "completed": "success",
}

PREMIUM_FLASH_OK = "premium_ok"
PREMIUM_FLASH_TELEGRAM_FAILED = "premium_telegram_failed"

TELEGRAM_API_BASE = "https://api.telegram.org"
_TELEGRAM_TIMEOUT = 15.0
_RECEIPT_CHUNK_SIZE = 64 * 1024


@public_router.get("/login", response_class=HTMLResponse, response_model=None)
def admin_login_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": None},
    )


@public_router.post("/login")
@login_limiter.limit(settings.rate_limit_login)
def admin_login(
    request: Request,
    db: Session = Depends(get_db_session),
    username: str = Form(...),
    password: str = Form(...),
):
    identity = verify_admin_credentials(username, password, db)
    if identity is None:
        logger.warning("Admin panelga muvaffaqiyatsiz kirish urinishi")
        audit_service.record(
            db,
            None,
            audit_service.LOGIN_FAILED,
            detail={"login": (username or "")[:32]},
        )
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"error": "Login yoki parol noto‘g‘ri"},
            status_code=401,
        )
    # Session fixation'ga qarshi: kirishdan oldin eski sessiya tarkibi tashlanadi.
    start_admin_session(request, identity)
    audit_service.record(db, identity, audit_service.LOGIN_SUCCESS)
    return RedirectResponse(url="/admin", status_code=303)


@public_router.get("/logout")
def admin_logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("", response_class=HTMLResponse, response_model=None)
@requires(VIEW_AGGREGATE)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    range: int = Query(default=30, ge=0, le=365),
    variant: str | None = Query(default=None),
) -> Response:
    service = AdminAnalyticsService(db)
    variants = service.variant_stats()
    known = [row.variant for row in variants]
    chosen = variant if variant in known else None
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "stats": service.dashboard_stats(),
            "growth": service.growth_stats(),
            # Bitta to'plam bo'lsa taqqoslashning ma'nosi yo'q.
            "variants": variants if len(variants) > 1 else [],
            "funnel": service.funnel(days=range or None, variant=chosen),
            "range_options": (7, 30, 90, 0),
            "current_range": range,
            "variant_options": known,
            "current_variant": chosen,
            "admin": admin,
        },
    )


@router.get("/sessions", response_class=HTMLResponse, response_model=None)
@requires(VIEW_PII)
def admin_sessions_list(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = "all",
    code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
) -> Response:
    service = AdminAnalyticsService(db)
    result = service.list_sessions_page(
        status_filter=filter,
        payment_code=code,
        page=normalize_page(page),
        page_size=DEFAULT_PAGE_SIZE,
    )
    session_codes = {s.id: payment_code_for_session(db, s) for s in result.items}
    return templates.TemplateResponse(
        request,
        "admin/sessions.html",
        {
            "sessions": result.items,
            "session_codes": session_codes,
            "current_filter": filter,
            "status_badge": STATUS_BADGE,
            "search_code": (code or "").strip(),
            "pagination": result,
        },
    )


@router.get("/sessions/{session_id}", response_class=HTMLResponse, response_model=None)
@requires(VIEW_PII)
def admin_session_detail(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db_session),
) -> Response:
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
@requires(VIEW_PII)
def admin_personality_sessions_legacy() -> RedirectResponse:
    return RedirectResponse(url="/admin/sessions", status_code=303)


def _redirect_with_flash(url: str, flash: str | None = None) -> RedirectResponse:
    if flash:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}flash={quote(flash)}"
    return RedirectResponse(url=url, status_code=303)


def _grant_premium_redirect_target(return_to: str, session_id: int) -> str:
    if return_to == "sessions":
        return "/admin/sessions"
    if return_to == "premium":
        return "/admin/premium-requests"
    return f"/admin/sessions/{session_id}"


def _admin_grant_premium_session(
    session_id: int,
    db: Session,
    admin: AdminIdentity,
    *,
    return_to: str,
) -> RedirectResponse:
    outcome = PremiumPaymentService(db).grant_manual_premium(
        session_id, approved_by=admin.audit_actor
    )
    redirect_url = _grant_premium_redirect_target(return_to, session_id)
    if outcome.code == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessiya topilmadi")
    if outcome.code == "incomplete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Testni tugatmagan sessiyaga premium berib bo‘lmaydi",
        )
    if outcome.code == "granted" and outcome.session is not None:
        audit_service.record(
            db,
            admin,
            audit_service.MANUAL_PREMIUM_GRANTED,
            target_type="session",
            target_id=session_id,
            detail={"session_id": session_id},
        )
        return _redirect_with_flash(redirect_url, PREMIUM_FLASH_OK)
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/personality/{session_id}/grant-premium")
@requires(MODERATE_PAYMENTS)
def admin_grant_premium_legacy(
    session_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    return_to: str = Query(default="detail"),
) -> RedirectResponse:
    return _admin_grant_premium_session(session_id, db, admin, return_to=return_to)


@router.post("/sessions/{session_id}/grant-premium")
@requires(MODERATE_PAYMENTS)
def admin_grant_premium(
    session_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    return_to: str = Query(default="sessions"),
) -> RedirectResponse:
    return _admin_grant_premium_session(session_id, db, admin, return_to=return_to)


@router.get("/premium-requests", response_class=HTMLResponse, response_model=None)
@requires(VIEW_PII)
def admin_premium_requests(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = "all",
    code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
) -> Response:
    repo = PaymentRepository(db)
    current_page = normalize_page(page)
    session_ids: list[int] | None = None
    search_code = (code or "").strip()
    if search_code:
        session_ids = [s.id for s in find_sessions_by_payment_code(db, search_code)]
    payments = repo.list_for_admin(
        status_filter=filter,
        session_ids=session_ids,
        limit=DEFAULT_PAGE_SIZE,
        offset=(current_page - 1) * DEFAULT_PAGE_SIZE,
    )
    result = Page(
        items=payments,
        total=repo.count_for_admin(status_filter=filter, session_ids=session_ids),
        page=current_page,
        page_size=DEFAULT_PAGE_SIZE,
    )
    session_codes = {
        p.session_id: payment_code_for_session(db, p.session)
        for p in payments
        if p.session is not None
    }
    return templates.TemplateResponse(
        request,
        "admin/premium_requests.html",
        {
            "payments": result.items,
            "session_codes": session_codes,
            "current_filter": filter,
            "search_code": search_code,
            "pagination": result,
            "format_price": format_price_uzs,
        },
    )


@router.post("/premium-requests/{payment_id}/approve")
@requires(MODERATE_PAYMENTS)
def admin_premium_approve(
    payment_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
) -> RedirectResponse:
    service = PremiumPaymentService(db)
    outcome = service.approve_payment(payment_id, approved_by=admin.audit_actor)
    url = "/admin/premium-requests"
    if outcome.code == "approved":
        audit_service.record(
            db, admin, audit_service.PAYMENT_APPROVED, target_type="payment", target_id=payment_id
        )
        session_id = outcome.session.id if outcome.session else None
        warning = (
            try_deliver_premium_approved_message(db, session_id=session_id)
            if session_id is not None
            else "Telegram xabari yuborilmadi."
        )
        if warning:
            return _redirect_with_flash(url, PREMIUM_FLASH_TELEGRAM_FAILED)
        return _redirect_with_flash(url, PREMIUM_FLASH_OK)
    if outcome.code == "already_approved":
        return RedirectResponse(url=url, status_code=303)
    return RedirectResponse(url=url, status_code=303)


@router.post("/premium-requests/{payment_id}/resend-telegram")
@requires(MODERATE_PAYMENTS)
def admin_premium_resend_telegram(
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    payment = PaymentRepository(db).get_by_id_with_session(payment_id)
    url = "/admin/premium-requests"
    if payment is None or payment.session is None or not payment.session.is_premium:
        return RedirectResponse(url=url, status_code=303)
    warning = try_deliver_premium_approved_message(db, session_id=payment.session.id)
    if warning:
        return _redirect_with_flash(url, PREMIUM_FLASH_TELEGRAM_FAILED)
    return _redirect_with_flash(url, PREMIUM_FLASH_OK)


@router.post("/premium-requests/{payment_id}/reject")
@requires(MODERATE_PAYMENTS)
def admin_premium_reject(
    payment_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
) -> RedirectResponse:
    outcome = PremiumPaymentService(db).reject_payment(payment_id, approved_by=admin.audit_actor)
    if outcome.code == "rejected":
        audit_service.record(
            db, admin, audit_service.PAYMENT_REJECTED, target_type="payment", target_id=payment_id
        )
    return RedirectResponse(url="/admin/premium-requests", status_code=303)


@router.get("/premium-requests/{payment_id}/receipt", response_model=None)
@requires(VIEW_PII)
def admin_premium_receipt(
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> StreamingResponse:
    """Chek rasmini Telegram'dan proxy qiladi: bot tokeni brauzerga chiqmaydi."""
    token = (settings.bot_token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOT_TOKEN sozlanmagan — chekni ko‘rsatib bo‘lmaydi",
        )

    payment = PaymentRepository(db).get_by_id(payment_id)
    if payment is None or not payment.receipt_file_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu to‘lov uchun chek yo‘q")

    file_path = _telegram_file_path(token, payment.receipt_file_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chek fayli Telegram’dan olinmadi",
        )

    # Manzil qat'iy Telegram API hosti ustiga quriladi, file_path esa yuqorida tekshirilgan.
    file_url = f"{TELEGRAM_API_BASE}/file/bot{token}/{quote(file_path, safe='/')}"
    try:
        connection = urlopen(file_url, timeout=_TELEGRAM_TIMEOUT)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("Telegram chek faylini yuklab bo‘lmadi: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chek faylini yuklab bo‘lmadi",
        ) from None

    media_type = connection.headers.get("Content-Type") or _guess_media_type(file_path)
    return StreamingResponse(
        _stream_connection(connection),
        media_type=media_type,
        headers={"Cache-Control": "private, no-store"},
    )


def _guess_media_type(file_path: str) -> str:
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed or "application/octet-stream"


def _telegram_file_path(token: str, file_id: str) -> str | None:
    """getFile natijasidan nisbiy fayl yo'lini oladi (xato bo'lsa None)."""
    query = urlencode({"file_id": file_id})
    try:
        with urlopen(
            f"{TELEGRAM_API_BASE}/bot{token}/getFile?{query}", timeout=_TELEGRAM_TIMEOUT
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        # Xato matnida so'rov manzili bo'lishi mumkin, shuning uchun faqat sinf nomi yoziladi.
        logger.warning("Telegram getFile muvaffaqiyatsiz: %s", type(exc).__name__)
        return None

    if not isinstance(payload, dict) or not payload.get("ok"):
        return None
    file_path = (payload.get("result") or {}).get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    if file_path.startswith("/") or ".." in file_path:
        return None
    return file_path


def _stream_connection(connection: HTTPResponse) -> Iterator[bytes]:
    with connection:
        while True:
            chunk = connection.read(_RECEIPT_CHUNK_SIZE)
            if not chunk:
                return
            yield chunk


# --- Eksport ---


def _csv_response(file: csv_export.CsvFile) -> Response:
    # Fayl nomi faqat ASCII; RFC 5987 shakli kelajakda nom o'zgarsa ham xavfsiz qoladi.
    encoded = quote(file.filename)
    disposition = f"attachment; filename=\"{file.filename}\"; filename*=UTF-8''{encoded}"
    return Response(
        content=file.content,
        media_type="text/csv",
        headers={
            "Content-Disposition": disposition,
            # Shaxsiy ma'lumotli fayl keshda qolmasligi kerak.
            "Cache-Control": "private, no-store, max-age=0",
            "Pragma": "no-cache",
            "X-Robots-Tag": "noindex, nofollow",
        },
    )


def _export_error(exc: Exception) -> HTTPException:
    if isinstance(exc, csv_export.ExportTooLarge):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Juda ko‘p qator ({exc.total} > {exc.limit}). Sana oralig‘ini toraytiring.",
        )
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/export/sessions.csv", response_model=None)
@requires(EXPORT_DATA)
def admin_export_sessions(
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    filter: str = Query(default="all"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> Response:
    try:
        filters = csv_export.session_filters(filter, date_from, date_to)
        file = csv_export.export_sessions(db, filters)
    except (csv_export.ExportFilterError, csv_export.ExportTooLarge) as exc:
        raise _export_error(exc) from None

    # Audit yozuvi javobdan OLDIN saqlanadi: yuklab olish uzilib qolsa ham
    # "kim nimani chiqardi" yozuvi qolishi kerak.
    audit_service.record(
        db,
        admin,
        audit_service.EXPORT_SESSIONS,
        detail={"filtr": filters.describe(), "qator": file.rows},
    )
    db.commit()
    return _csv_response(file)


@router.get("/export/payments.csv", response_model=None)
@requires(EXPORT_DATA)
def admin_export_payments(
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    filter: str = Query(default="all"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> Response:
    try:
        filters = csv_export.payment_filters(filter, date_from, date_to)
        file = csv_export.export_payments(db, filters)
    except (csv_export.ExportFilterError, csv_export.ExportTooLarge) as exc:
        raise _export_error(exc) from None

    audit_service.record(
        db,
        admin,
        audit_service.EXPORT_PAYMENTS,
        detail={"filtr": filters.describe(), "qator": file.rows},
    )
    db.commit()
    return _csv_response(file)


# --- Adminlar ---


@router.get("/users", response_class=HTMLResponse, response_model=None)
@requires(MANAGE_USERS)
def admin_users(
    request: Request,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    error: str | None = Query(default=None),
) -> Response:
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {
            "users": AdminRepository(db).list_users(),
            "roles": list(AdminRole),
            "role_label": role_label,
            "admin": admin,
            "error": error,
            "env_login": settings.admin_env_login_enabled,
            "env_username": admin_service.env_admin_username(),
        },
    )


def _users_redirect(error: str | None = None) -> RedirectResponse:
    target = "/admin/users" + (f"?error={quote(error)}" if error else "")
    return RedirectResponse(url=target, status_code=303)


@router.post("/users", response_model=None)
@requires(MANAGE_USERS)
def admin_users_create(
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(default=AdminRole.MODERATOR.value),
    telegram_user_id: str = Form(default=""),
) -> Response:
    try:
        chosen = AdminRole(role)
    except ValueError:
        return _users_redirect("Noma'lum rol")

    telegram_id: int | None = None
    cleaned_id = (telegram_user_id or "").strip()
    if cleaned_id:
        try:
            telegram_id = int(cleaned_id)
        except ValueError:
            return _users_redirect("Telegram ID raqam bo'lishi kerak")

    result = admin_service.create_user(
        db, username=username, password=password, role=chosen, telegram_user_id=telegram_id
    )
    if not result.ok or result.user is None:
        return _users_redirect(result.error)
    audit_service.record(
        db,
        admin,
        audit_service.USER_CREATED,
        target_type="admin_user",
        target_id=result.user.id,
        detail={"login": result.user.username, "rol": chosen.value},
    )
    return _users_redirect()


@router.post("/users/{user_id}/role", response_model=None)
@requires(MANAGE_USERS)
def admin_users_role(
    user_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    role: str = Form(...),
) -> Response:
    user = AdminRepository(db).get_by_id(user_id)
    if user is None:
        return _users_redirect("Hisob topilmadi")
    try:
        chosen = AdminRole(role)
    except ValueError:
        return _users_redirect("Noma'lum rol")

    result = admin_service.set_role(db, user, chosen, actor=admin)
    if not result.ok:
        return _users_redirect(result.error)
    audit_service.record(
        db,
        admin,
        audit_service.USER_ROLE_CHANGED,
        target_type="admin_user",
        target_id=user_id,
        detail={"login": user.username, "rol": chosen.value},
    )
    return _users_redirect()


@router.post("/users/{user_id}/active", response_model=None)
@requires(MANAGE_USERS)
def admin_users_active(
    user_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    active: str = Form(default="0"),
) -> Response:
    user = AdminRepository(db).get_by_id(user_id)
    if user is None:
        return _users_redirect("Hisob topilmadi")

    wanted = active == "1"
    result = admin_service.set_active(db, user, wanted, actor=admin)
    if not result.ok:
        return _users_redirect(result.error)
    audit_service.record(
        db,
        admin,
        audit_service.USER_ACTIVATED if wanted else audit_service.USER_DEACTIVATED,
        target_type="admin_user",
        target_id=user_id,
        detail={"login": user.username},
    )
    return _users_redirect()


@router.post("/users/{user_id}/password", response_model=None)
@requires(MANAGE_USERS)
def admin_users_password(
    user_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    password: str = Form(...),
) -> Response:
    user = AdminRepository(db).get_by_id(user_id)
    if user is None:
        return _users_redirect("Hisob topilmadi")
    result = admin_service.set_password(db, user, password)
    if not result.ok:
        return _users_redirect(result.error)
    audit_service.record(
        db,
        admin,
        audit_service.USER_PASSWORD_CHANGED,
        target_type="admin_user",
        target_id=user_id,
        detail={"login": user.username},
    )
    return _users_redirect()


# --- Audit jurnali ---


@router.get("/audit", response_class=HTMLResponse, response_model=None)
@requires(VIEW_AUDIT)
def admin_audit(
    request: Request,
    db: Session = Depends(get_db_session),
    action: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
) -> Response:
    repo = AdminRepository(db)
    current = normalize_page(page)
    entries = repo.list_audit(
        action=action, limit=DEFAULT_PAGE_SIZE, offset=(current - 1) * DEFAULT_PAGE_SIZE
    )
    pagination = Page(
        items=entries,
        total=repo.count_audit(action=action),
        page=current,
        page_size=DEFAULT_PAGE_SIZE,
    )
    return templates.TemplateResponse(
        request,
        "admin/audit.html",
        {
            "entries": entries,
            "pagination": pagination,
            "current_action": action,
            "actions": sorted(audit_service.NEVER_PURGED_ACTIONS | {audit_service.LOGIN_SUCCESS}),
        },
    )


# --- Bildirishnoma navbati ---


@router.get("/notifications", response_class=HTMLResponse, response_model=None)
@requires(VIEW_OPS)
def admin_notifications(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = Query(default="pending"),
    page: int = Query(default=1, ge=1),
) -> Response:
    current = normalize_page(page)
    rows, total = notification_outbox.list_for_admin(
        db,
        status_filter=filter,
        limit=DEFAULT_PAGE_SIZE,
        offset=(current - 1) * DEFAULT_PAGE_SIZE,
    )
    seen_at = notification_outbox.heartbeat_seen_at(db, OUTBOX_WORKER_HEARTBEAT)
    return templates.TemplateResponse(
        request,
        "admin/notifications.html",
        {
            "rows": rows,
            "pagination": Page(items=rows, total=total, page=current, page_size=DEFAULT_PAGE_SIZE),
            "current_filter": filter,
            "health": notification_outbox.health(db, worker_seen_at=seen_at),
            "statuses": notification_outbox.ADMIN_STATUS_FILTERS,
            "now": utcnow(),
            "overdue_minutes": settings.outbox_overdue_minutes,
        },
    )


@router.post("/notifications/{outbox_id}/retry", response_model=None)
@requires(VIEW_OPS)
def admin_notification_retry(
    outbox_id: int,
    db: Session = Depends(get_db_session),
    admin: AdminIdentity = Depends(current_admin),
    filter: str = Form(default="failed"),
) -> RedirectResponse:
    if notification_outbox.retry_now(db, outbox_id):
        audit_service.record(
            db,
            admin,
            audit_service.NOTIFICATION_RETRIED,
            target_type="notification",
            target_id=outbox_id,
        )
    return RedirectResponse(url=f"/admin/notifications?filter={quote(filter)}", status_code=303)


# --- Saqlash siyosati ---


@router.get("/retention", response_class=HTMLResponse, response_model=None)
@requires(VIEW_OPS)
def admin_retention(
    request: Request,
    db: Session = Depends(get_db_session),
) -> Response:
    """Faqat hisobot.

    O'chirish ATAYLAB bu yerda emas: `python -m app.retention --apply`. Shunda
    brauzerdagi ikkinchi bosish yoki proksi timeouti yarim bajarilgan tozalashga
    olib kelmaydi, hech qanday qulf va CSRF himoyasi ham kerak bo'lmaydi.
    """
    report = retention_service.run(db, dry_run=True)
    return templates.TemplateResponse(
        request,
        "admin/retention.html",
        {
            "report": report,
            "labels": retention_service.RULE_LABELS,
            "last_run": notification_outbox.heartbeat_seen_at(db, RETENTION_HEARTBEAT),
        },
    )

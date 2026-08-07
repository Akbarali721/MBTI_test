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
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.config import settings
from app.dependencies import get_db_session, require_admin, verify_admin_credentials
from app.personality.payment_code import payment_code_for_session
from app.repositories.payment_repository import PaymentRepository
from app.services.admin_analytics_service import (
    DEFAULT_PAGE_SIZE,
    AdminAnalyticsService,
    Page,
    normalize_page,
)
from app.services.personality_service import PersonalityService
from app.services.premium_payment_service import PremiumPaymentService, format_price_uzs
from app.templating import templates

logger = logging.getLogger(__name__)

# Autentifikatsiyasiz ochiq qoladigan yagona marshrutlar.
public_router = APIRouter(prefix="/admin", tags=["admin"])
# Qolgan hamma narsa: himoya router darajasida, shuning uchun yangi endpoint
# qo'shilganda uni himoyalashni unutib bo'lmaydi.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

login_limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    storage_uri=settings.rate_limit_storage_uri,
)

STATUS_BADGE = {
    "visited": "secondary",
    "started": "info",
    "in_progress": "warning",
    "completed": "success",
}

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
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_admin_credentials(username, password):
        logger.warning("Admin panelga muvaffaqiyatsiz kirish urinishi")
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"error": "Login yoki parol noto‘g‘ri"},
            status_code=401,
        )
    # Session fixation'ga qarshi: kirishdan oldin eski sessiya tarkibi tashlanadi.
    request.session.clear()
    request.session["admin_authenticated"] = True
    return RedirectResponse(url="/admin", status_code=303)


@public_router.get("/logout")
def admin_logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("", response_class=HTMLResponse, response_model=None)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db_session),
) -> Response:
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
def admin_personality_sessions_legacy() -> RedirectResponse:
    return RedirectResponse(url="/admin/sessions", status_code=303)


@router.post("/personality/{session_id}/grant-premium")
def admin_grant_premium(
    session_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    PersonalityService(db).grant_premium(session_id)
    return RedirectResponse(url=f"/admin/sessions/{session_id}", status_code=303)


@router.get("/premium-requests", response_class=HTMLResponse, response_model=None)
def admin_premium_requests(
    request: Request,
    db: Session = Depends(get_db_session),
    filter: str = "all",
    page: int = Query(default=1, ge=1),
) -> Response:
    repo = PaymentRepository(db)
    current_page = normalize_page(page)
    payments = repo.list_for_admin(
        status_filter=filter,
        limit=DEFAULT_PAGE_SIZE,
        offset=(current_page - 1) * DEFAULT_PAGE_SIZE,
    )
    result = Page(
        items=payments,
        total=repo.count_for_admin(status_filter=filter),
        page=current_page,
        page_size=DEFAULT_PAGE_SIZE,
    )
    return templates.TemplateResponse(
        request,
        "admin/premium_requests.html",
        {
            "payments": result.items,
            "current_filter": filter,
            "pagination": result,
            "format_price": format_price_uzs,
        },
    )


@router.post("/premium-requests/{payment_id}/approve")
def admin_premium_approve(
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    PremiumPaymentService(db).approve_payment(payment_id, approved_by="web-admin")
    return RedirectResponse(url="/admin/premium-requests", status_code=303)


@router.post("/premium-requests/{payment_id}/reject")
def admin_premium_reject(
    payment_id: int,
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    PremiumPaymentService(db).reject_payment(payment_id, approved_by="web-admin")
    return RedirectResponse(url="/admin/premium-requests", status_code=303)


@router.get("/premium-requests/{payment_id}/receipt", response_model=None)
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

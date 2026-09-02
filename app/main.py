import logging
from contextlib import asynccontextmanager
from html import escape
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.database import engine
from app.observability import (
    RequestLoggingMiddleware,
    configure_logging,
    init_sentry,
)
from app.paths import STATIC_DIR
from app.routers import admin, personality, relationship, share, team
from app.templating import render_template_or_none

logger = logging.getLogger(__name__)

configure_logging()
init_sentry()

HOME_URL = "/"


class SecurityHeadersMiddleware:
    """Barcha javoblarga xavfsizlik sarlavhalarini qo'shadi (mavjudini bosib o'tmaydi)."""

    def __init__(self, app: ASGIApp, headers: dict[str, str]) -> None:
        self.app = app
        self.headers = {key: value for key, value in headers.items() if value}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                for key, value in self.headers.items():
                    if key not in response_headers:
                        response_headers.append(key, value)
            await send(message)

        await self.app(scope, receive, send_wrapper)


def _security_headers() -> dict[str, str]:
    headers = {
        # Admin tasdiqlash tugmalari clickjacking bilan bosilmasligi uchun.
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        "Content-Security-Policy": settings.content_security_policy,
    }
    if settings.secure_cookies_enabled:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Sxema "alembic upgrade head", kontent esa "python -m app.seed" orqali boshqariladi.
    logger.info("MBTI platformasi ishga tushdi")
    yield


app = FastAPI(
    title="MBTI Platform",
    lifespan=lifespan,
    # Interaktiv hujjatlar admin endpointlarining to'liq ro'yxatini oshkor qiladi,
    # shuning uchun ular faqat ishlab chiqish rejimida ochiq.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

app.state.limiter = admin.login_limiter

# add_middleware oxirgi qo'shilganni eng tashqi qatlamga qo'yadi: proxy sarlavhalari
# avval o'qilishi, sessiya esa eng ichkarida bo'lishi kerak.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    # Cookie'lar HTTPS'ga bog'lanadi va HSTS yoqiladi; lokal ishlab chiqishda o'chiq.
    https_only=settings.secure_cookies_enabled,
    max_age=settings.session_max_age,
)
app.add_middleware(SecurityHeadersMiddleware, headers=_security_headers())
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_proxy_hosts)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(personality.router)
app.include_router(admin.public_router)
app.include_router(admin.router)
app.include_router(relationship.router)
app.include_router(share.router)
app.include_router(team.router)


def _wants_html(request: Request) -> bool:
    """Brauzer HTML so'rayotgan bo'lsa yalang'och JSON qaytarmaymiz."""
    accept = request.headers.get("accept", "")
    return "text/html" in accept.lower()


def _fallback_error_html(status_code: int, title: str, message: str) -> str:
    return (
        '<!DOCTYPE html><html lang="uz"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)} — MBTI</title></head><body>"
        f"<h1>{status_code} — {escape(title)}</h1><p>{escape(message)}</p>"
        '<p><a href="/personality">Bosh sahifaga qaytish</a></p>'
        "</body></html>"
    )


def _error_copy(request: Request, status_code: int, message: str | None) -> tuple[str, str]:
    """Xato sarlavha va matni — tanlangan til bo'yicha (404 sahifada aralash til bo'lmasin)."""
    from app.i18n import resolve_lang, t

    lang = resolve_lang(request)
    title_key = f"errors.title_{status_code}"
    message_key = f"errors.message_{status_code}"
    title = t(title_key, lang)
    if title == title_key:
        title = t("errors.title_default", lang)
    text_message = message or t(message_key, lang)
    if text_message == message_key:
        text_message = t("errors.message_default", lang)
    return title, text_message


def error_response(request: Request, status_code: int, message: str | None = None) -> Response:
    """HTML so'ralganda shablonli xato sahifasi, aks holda JSON."""
    title, text_message = _error_copy(request, status_code, message)
    if not _wants_html(request):
        return JSONResponse({"detail": text_message}, status_code=status_code)

    context = {"status_code": status_code, "title": title, "message": text_message, "home_url": HOME_URL}
    for name in (f"errors/{status_code}.html", "errors/error.html"):
        # Shablonlar alohida qo'shiladi; bo'lmasa oddiy HTML bilan javob beramiz.
        rendered = render_template_or_none(request, name, context, status_code=status_code)
        if rendered is not None:
            return rendered
    return HTMLResponse(_fallback_error_html(status_code, title, text_message), status_code=status_code)


def _uzbek_detail(exc: StarletteHTTPException) -> str | None:
    """Framework'ning inglizcha standart matnini o'zbekcha xabar bilan almashtiradi."""
    detail = exc.detail if isinstance(exc.detail, str) else ""
    if not detail.strip():
        return None
    try:
        default_phrase = HTTPStatus(exc.status_code).phrase
    except ValueError:
        default_phrase = ""
    if detail.strip().casefold() == default_phrase.casefold():
        return None
    return detail


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    headers = dict(exc.headers or {})
    location = headers.get("Location") or headers.get("location")
    if location and 300 <= exc.status_code < 400:
        # require_admin kabi bog'liqliklar redirect'ni HTTPException orqali qaytaradi.
        return RedirectResponse(url=location, status_code=exc.status_code)
    response = error_response(request, exc.status_code, _uzbek_detail(exc))
    for key, value in headers.items():
        response.headers.setdefault(key, value)
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    logger.warning("So‘rov chegarasi oshib ketdi: %s", request.url.path)
    return error_response(request, 429)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    logger.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
    return error_response(request, 500)


@app.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health-check: bazaga ulanib bo‘lmadi")
        return JSONResponse({"status": "error", "database": "error"}, status_code=503)
    return JSONResponse({"status": "ok", "database": "ok"})


@app.get("/robots.txt", include_in_schema=False)
def robots() -> PlainTextResponse:
    # Token bilan ochiladigan sahifalar allaqachon noindex; bu yerda admin va
    # xizmat yo'llarini kraulerlardan butunlay chiqarib tashlaymiz.
    base = settings.public_base_url.rstrip("/")
    body = "\n".join(
        [
            "User-agent: *",
            "Disallow: /admin",
            "Disallow: /personality/test",
            "Disallow: /personality/result",
            "Allow: /",
            "",
            f"Sitemap: {base}/sitemap.xml",
            "",
        ]
    )
    return PlainTextResponse(body)


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    base = settings.public_base_url.rstrip("/")
    paths = ("/personality", "/personality/instructions")
    urls = "".join(f"<url><loc>{base}{path}</loc></url>" for path in paths)
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    return Response(content=body, media_type="application/xml")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/personality", status_code=303)


@app.get("/start", include_in_schema=False)
@app.get("/home", include_in_schema=False)
@app.get("/webapp", include_in_schema=False)
@app.get("/app", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
def legacy_web_entry() -> RedirectResponse:
    """Eski/noto'g'ri kirish yo'llari — bosh sahifaga."""
    return RedirectResponse(url=HOME_URL, status_code=303)


@app.get("/uz", include_in_schema=False)
def legacy_lang_uz() -> RedirectResponse:
    return RedirectResponse(url="/?lang=uz", status_code=303)


@app.get("/ru", include_in_schema=False)
def legacy_lang_ru() -> RedirectResponse:
    return RedirectResponse(url="/?lang=ru", status_code=303)

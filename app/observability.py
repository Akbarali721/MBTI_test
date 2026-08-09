from __future__ import annotations

import logging
import logging.config
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings

request_logger = logging.getLogger("app.request")
logger = logging.getLogger(__name__)

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s %(message)s"
# So'rov loglari shovqin qilmasligi uchun DEBUG darajasiga tushiriladigan yo'llar.
_QUIET_PREFIXES = ("/static", "/health", "/favicon.ico")


def configure_logging() -> None:
    """Root logger'ni bir marta sozlaydi; uvicorn o'z loggerlarini saqlab qoladi."""
    level = settings.log_level.strip().upper() or "INFO"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": {"format": _LOG_FORMAT}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                # uvicorn access log konkret yo'lni yozadi — natija tokeni log'ga tushadi.
                # O'rniga RequestLoggingMiddleware marshrut shablonini yozadi.
                # Eski xatti-harakat kerak bo'lsa: ACCESS_LOG=true.
                "uvicorn.access": {"level": "INFO" if settings.access_log else "WARNING"},
                "sqlalchemy.engine": {"level": "WARNING"},
                # passlib 1.7.4 bcrypt >= 4.1 da olib tashlangan __about__ ni o'qimoqchi
                # bo'ladi va xatoni ERROR sifatida yozadi. Xato ushlanadi, hashlash
                # ishlayveradi — lekin traceback Sentry'ga soxta hodisa bo'lib tushadi.
                "passlib.handlers.bcrypt": {"level": "CRITICAL"},
            },
        }
    )


def init_sentry() -> bool:
    """SENTRY_DSN berilgan bo'lsa Sentry'ni yoqadi. Qaytaradi: yoqildimi."""
    dsn = (settings.sentry_dsn or "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logger.warning("SENTRY_DSN berilgan, lekin sentry-sdk o'rnatilmagan — o'tkazib yuborildi")
        return False

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment="development" if settings.debug else "production",
        # Foydalanuvchi ma'lumotlari (IP, cookie, session) Sentry'ga yuborilmaydi.
        send_default_pii=False,
    )
    logger.info("Sentry yoqildi")
    return True


def _log_path(scope: Scope) -> str:
    """Token va boshqa maxfiy qiymatlar log'ga tushmasligi uchun marshrut shabloni."""
    route = scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return str(route_path)
    return str(scope.get("path", "-"))


class RequestLoggingMiddleware:
    """Har bir HTTP so'rovi uchun metod, marshrut, status va davomiylikni yozadi.

    Query string ham, konkret yo'l parametrlari ham log'ga tushmaydi: natija
    tokeni yoki to'lov kodi log fayliga sizib chiqmasligi kerak.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000.0
            raw_path = str(scope.get("path", "-"))
            if status_code >= 500:
                level = logging.ERROR
            elif raw_path.startswith(_QUIET_PREFIXES):
                level = logging.DEBUG
            else:
                level = logging.INFO
            request_logger.log(
                level,
                "%s %s -> %s (%.1f ms)",
                scope.get("method", "-"),
                _log_path(scope),
                status_code,
                duration_ms,
            )

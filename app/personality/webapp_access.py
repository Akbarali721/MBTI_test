"""Telegram WebApp talabi va lokal DEV_MODE (production xavfsizligi bilan)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from starlette.requests import Request

from app.config import LOCAL_URL_HOSTS, settings
from app.personality.analytics_constants import DEFAULT_SOURCE, DEV_BROWSER_SOURCE
from app.personality.session_binding import get_bound_session

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.personality import PersonalityTestSession

_TOKEN_ROUTE = re.compile(
    r"^/personality/(?:test|result)/[0-9a-f]{32}",
    re.IGNORECASE,
)

# WebApp ichida bind skripti ishlashi uchun ochiq qoladigan sahifalar.
_FUNNEL_PATHS = frozenset(
    {
        "/personality",
        "/personality/instructions",
        "/personality/intent",
        "/personality/appearance",
        "/personality/start",
    }
)


def dev_mode_active() -> bool:
    return settings.dev_mode_active


def _local_host(host_header: str | None) -> bool:
    host = (host_header or "").split(":")[0].strip().lower()
    if host in LOCAL_URL_HOSTS:
        return True
    # Starlette TestClient default host (faqat DEBUG/test muhitida).
    return settings.debug and host == "testserver"


def dev_mode_bypasses_webapp_gate(request: Request | None) -> bool:
    """DEV_MODE: WebApp talabi faqat lokal Host (127.0.0.1/localhost) da o‘chiriladi."""
    if settings._railway_environment():
        return False
    if not (settings.dev_mode and settings.debug):
        return False
    if request is None:
        return False
    return _local_host(request.headers.get("host"))


def telegram_webapp_gate_enabled(request: Request | None = None) -> bool:
    if not settings.telegram_webapp_only:
        return False
    return not dev_mode_bypasses_webapp_gate(request)


def is_dev_browser_session(session: PersonalityTestSession | None) -> bool:
    if session is None:
        return False
    if session.source == DEV_BROWSER_SOURCE:
        return True
    return session.telegram_user_id == settings.dev_browser_telegram_id


def ensure_dev_browser_telegram_user(db: Session) -> None:
    """Lokal DEV: feedback FK va analytics uchun test Telegram qatori (faqat sqlite dev)."""
    if settings._railway_environment() or not (settings.dev_mode and settings.debug):
        return
    if not settings.database_url.startswith("sqlite"):
        return
    from app.services.telegram_user_service import (
        TelegramProfileInput,
        get_by_telegram_id,
        upsert_from_webapp,
    )

    tid = settings.dev_browser_telegram_id
    if get_by_telegram_id(db, tid) is not None:
        return
    upsert_from_webapp(
        db,
        TelegramProfileInput(
            telegram_id=tid,
            username="dev_browser",
            first_name="Dev",
            last_name="Browser",
        ),
    )


def attach_dev_browser_user(db: Session, session: PersonalityTestSession) -> None:
    ensure_dev_browser_telegram_user(db)
    tid = settings.dev_browser_telegram_id
    if session.telegram_user_id is not None and session.telegram_user_id != tid:
        return
    session.telegram_user_id = tid
    if not session.source or session.source == DEFAULT_SOURCE:
        session.source = DEV_BROWSER_SOURCE
    db.flush()


def mark_webapp_bound(request: Request) -> None:
    request.session["telegram_webapp_bound"] = True


def mark_dev_browser(request: Request) -> None:
    request.session["personality_dev_browser"] = True


def _browser_access_ok(request: Request) -> bool:
    return bool(request.session.get("telegram_webapp_bound")) or (
        bool(request.session.get("personality_dev_browser")) and dev_mode_bypasses_webapp_gate(request)
    )


def _session_allows_protected_route(
    session: PersonalityTestSession | None,
    request: Request,
) -> bool:
    if session is None:
        return False
    if is_dev_browser_session(session):
        return dev_mode_bypasses_webapp_gate(request)
    tid = session.telegram_user_id
    return tid is not None and tid != 0


def allows_personality_path(request: Request, path: str, db: Session | None = None) -> bool:
    if dev_mode_bypasses_webapp_gate(request):
        return True
    if not telegram_webapp_gate_enabled(request):
        return True

    normalized = path.split("?", 1)[0].rstrip("/") or "/"

    if normalized == "/personality/telegram-bind":
        return True

    if normalized in _FUNNEL_PATHS:
        return True

    if request.method.upper() == "POST" and normalized in {
        "/personality/begin",
        "/personality/restart",
        "/personality/start",
        "/personality/intent",
        "/personality/appearance",
    }:
        return True

    if _TOKEN_ROUTE.match(normalized):
        if _browser_access_ok(request):
            return True
        if db is not None:
            return _session_allows_protected_route(get_bound_session(request, db), request)
        return False

    if normalized.startswith("/personality/"):
        if _browser_access_ok(request):
            return True
        if db is not None:
            return _session_allows_protected_route(get_bound_session(request, db), request)
        return False

    return True


class LocalDevBrowserMiddleware:
    """Lokal DEV: Starlette sessiyasida dev-browser bayrog‘ini gate’dan oldin qo‘yadi."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "http":
            path = scope.get("path") or ""
            if path == "/" or path.startswith("/personality"):
                from starlette.requests import Request

                request = Request(scope, receive)
                if dev_mode_bypasses_webapp_gate(request):
                    mark_dev_browser(request)
        await self.app(scope, receive, send)


def local_dev_entry_redirect(request: Request) -> bool:
    """GET / lokal dev kirish nuqtasi (PUBLIC_BASE_URL prod bo‘lsa ham Host lokal bo‘lishi mumkin)."""
    if settings.dev_mode_active:
        return True
    return dev_mode_bypasses_webapp_gate(request)

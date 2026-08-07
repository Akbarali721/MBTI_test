from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.authz import AdminIdentity, required_permission
from app.config import settings
from app.database import get_db
from app.services.admin_service import authenticate, resolve_web_identity

logger = logging.getLogger(__name__)

ADMIN_LOGIN_URL = "/admin/login"
# Router darajasida ulanganda login/logout sahifalari qulflanib qolmasligi kerak.
ADMIN_PUBLIC_PATHS = frozenset({ADMIN_LOGIN_URL, "/admin/logout"})

SESSION_AUTH_KEY = "admin_authenticated"
SESSION_USER_ID_KEY = "admin_user_id"
SESSION_USERNAME_KEY = "admin_username"
SESSION_LOGIN_AT_KEY = "admin_login_at"

FORBIDDEN_MESSAGE = "Bu bo‘lim uchun huquqingiz yo‘q."


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def start_admin_session(request: Request, identity: AdminIdentity) -> None:
    """Sessiyaga faqat identifikator yoziladi — rol emas.

    Rol har so'rovda bazadan o'qiladi, aks holda rolni pasaytirish yoki hisobni
    o'chirish ochiq sessiyaga ta'sir qilmasdi.
    """
    request.session.clear()
    request.session[SESSION_AUTH_KEY] = True
    request.session[SESSION_USER_ID_KEY] = identity.user_id
    request.session[SESSION_USERNAME_KEY] = identity.username
    request.session[SESSION_LOGIN_AT_KEY] = datetime.now(timezone.utc).timestamp()


def _redirect_to_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        detail="Avval admin sifatida kiring",
        headers={"Location": ADMIN_LOGIN_URL},
    )


def _session_expired(request: Request) -> bool:
    """Mutlaq muddat.

    Starlette cookie'ni har javobda qayta imzolaydi, ya'ni SESSION_MAX_AGE aslida
    "faoliyatsizlik" muddati bo'lib qoladi. Kirish vaqti sessiyada saqlanadi va
    shu yerda qat'iy chegara sifatida tekshiriladi.
    """
    raw = request.session.get(SESSION_LOGIN_AT_KEY)
    if not isinstance(raw, (int, float)):
        return True
    age = datetime.now(timezone.utc).timestamp() - float(raw)
    return age < 0 or age > settings.session_max_age


def require_admin(
    request: Request,
    db: Session = Depends(get_db_session),
) -> AdminIdentity | None:
    """Yagona tekshiruv nuqtasi: avval autentifikatsiya, so'ng ruxsat.

    Ruxsat reyestrda e'lon qilinmagan endpoint 403 beradi. Ya'ni yangi admin
    marshrutini qo'shib `@requires(...)` yozishni unutish "hamma ochadi" emas,
    "hech kim ocholmaydi" degani — nuqson xavfsiz tomonga og'adi.
    """
    if request.url.path in ADMIN_PUBLIC_PATHS:
        return None

    if request.session.get(SESSION_AUTH_KEY) is not True or _session_expired(request):
        request.session.clear()
        raise _redirect_to_login()

    username = request.session.get(SESSION_USERNAME_KEY)
    if not isinstance(username, str) or not username:
        # Eski (deploy paytida ochiq qolgan) cookie: ichida shaxs yo'q.
        request.session.clear()
        raise _redirect_to_login()

    raw_id = request.session.get(SESSION_USER_ID_KEY)
    if raw_id is not None and (isinstance(raw_id, bool) or not isinstance(raw_id, int)):
        # Buzilgan qiymatni jimgina None ga aylantirish `.env` egasi tarmog'iga
        # tushib ketishga olib kelardi — ya'ni xato xavfsiz tomonga og'imasdi.
        request.session.clear()
        raise _redirect_to_login()
    user_id = raw_id if isinstance(raw_id, int) else None

    identity = resolve_web_identity(db, user_id=user_id, username=username)
    if identity is None:
        request.session.clear()
        raise _redirect_to_login()

    route = request.scope.get("route")
    permission = required_permission(getattr(route, "endpoint", None))
    if permission is None or not identity.can(permission):
        logger.warning(
            "Admin ruxsati rad etildi: %s %s (rol=%s)",
            request.method,
            request.url.path,
            identity.role.value,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_MESSAGE)

    # Shablonlar navigatsiyani rol bo'yicha ko'rsatishi uchun (haqiqiy tekshiruv
    # baribir shu yerda bajarilgan).
    request.state.admin = identity
    return identity


def current_admin(identity: AdminIdentity | None = Depends(require_admin)) -> AdminIdentity:
    """Endpoint ichida amaldagi adminni olish (FastAPI bir so'rovda keshlaydi)."""
    if identity is None:
        raise _redirect_to_login()
    return identity


def verify_admin_credentials(username: str, password: str, db: Session) -> AdminIdentity | None:
    return authenticate(db, username, password)

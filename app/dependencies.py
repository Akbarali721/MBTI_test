import hmac
import secrets

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import hash_password, settings, verify_password
from app.database import get_db

ADMIN_LOGIN_URL = "/admin/login"
# Router darajasida ulanganda login/logout sahifalari qulflanib qolmasligi kerak.
ADMIN_PUBLIC_PATHS = frozenset({ADMIN_LOGIN_URL, "/admin/logout"})

_dummy_hash: str | None = None


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def require_admin(request: Request) -> None:
    if request.url.path in ADMIN_PUBLIC_PATHS:
        return
    if request.session.get("admin_authenticated") is not True:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Avval admin sifatida kiring",
            headers={"Location": ADMIN_LOGIN_URL},
        )


def _fallback_hash() -> str:
    """Parol hash'i sozlanmaganda ham verify bir xil vaqt olishi uchun dummy hash."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password(secrets.token_urlsafe(32))
    return _dummy_hash


def verify_admin_credentials(username: str, password: str) -> bool:
    expected_username = settings.admin_username
    expected_hash = settings.admin_password_hash or _fallback_hash()
    username_ok = hmac.compare_digest(username.encode("utf-8"), expected_username.encode("utf-8"))
    # Foydalanuvchi nomi noto'g'ri bo'lsa ham parol tekshiriladi: javob vaqti bir xil qoladi.
    password_ok = verify_password(password, expected_hash)
    return username_ok and password_ok

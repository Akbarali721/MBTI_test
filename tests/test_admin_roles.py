"""Ko'p admin, rollar va audit jurnali.

Eng muhim kafolat: ruxsat REYESTRDA e'lon qilinmagan admin marshruti ochiq
qolmaydi. Ya'ni yangi endpoint qo'shib `@requires(...)` yozishni unutish
"hamma ko'ra oladi" emas, "hech kim ko'ra olmaydi" degani.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

import pytest
from itsdangerous import TimestampSigner
from sqlalchemy import select

from app.authz import ALL_PERMISSIONS, PERMISSIONS, required_permission
from app.config import hash_password, settings
from app.models.admin import AdminAuditLog, AdminUser
from app.models.enums import AdminRole
from app.repositories.admin_repository import AdminRepository
from app.services import admin_service
from tests.helpers import admin_login, complete_session, db_session, session_by_token

PUBLIC_ADMIN_PATHS = {"/admin/login", "/admin/logout"}

PASSWORD = "juda-kuchli-parol-2026"


def _create(client, username: str, role: AdminRole, telegram_user_id: int | None = None):
    with db_session(client) as db:
        result = admin_service.create_user(
            db,
            username=username,
            password=PASSWORD,
            role=role,
            telegram_user_id=telegram_user_id,
        )
        assert result.ok, result.error
        db.commit()
        return result.user.id


def _login_as(client, username: str):
    response = client.post(
        "/admin/login",
        data={"username": username, "password": PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.status_code
    return response


# --------------------------------------------------------------------------- reyestr


def test_every_admin_route_declares_a_permission(client):
    """Ruxsatsiz qolgan marshrut testni yiqitadi — bu himoyaning asosiy tayanchi."""
    from app.main import app

    missing = []
    checked = 0
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/admin") or path in PUBLIC_ADMIN_PATHS:
            continue
        checked += 1
        permission = required_permission(getattr(route, "endpoint", None))
        if permission is None:
            missing.append(path)
        elif permission not in ALL_PERMISSIONS:
            missing.append(f"{path} -> {permission}")
    assert not missing, f"ruxsat e'lon qilinmagan marshrutlar: {missing}"
    assert checked >= 15


def test_role_permissions_are_strictly_nested():
    viewer = PERMISSIONS[AdminRole.VIEWER]
    moderator = PERMISSIONS[AdminRole.MODERATOR]
    owner = PERMISSIONS[AdminRole.OWNER]
    assert viewer < moderator < owner
    assert owner == ALL_PERMISSIONS


# --------------------------------------------------------------------------- rol matritsasi


ROLE_EXPECTATIONS = {
    AdminRole.VIEWER: {
        "/admin": 200,
        "/admin/sessions": 403,
        "/admin/premium-requests": 403,
        "/admin/export/sessions.csv": 403,
        "/admin/notifications": 403,
        "/admin/users": 403,
        "/admin/audit": 403,
    },
    AdminRole.MODERATOR: {
        "/admin": 200,
        "/admin/sessions": 200,
        "/admin/premium-requests": 200,
        "/admin/export/sessions.csv": 200,
        "/admin/notifications": 200,
        "/admin/users": 403,
        "/admin/audit": 403,
    },
    AdminRole.OWNER: {
        "/admin": 200,
        "/admin/sessions": 200,
        "/admin/premium-requests": 200,
        "/admin/export/sessions.csv": 200,
        "/admin/notifications": 200,
        "/admin/users": 200,
        "/admin/audit": 200,
    },
}


@pytest.mark.parametrize("role", list(AdminRole))
def test_each_role_sees_exactly_what_it_should(client, role):
    _create(client, f"rol-{role.value}", role)
    _login_as(client, f"rol-{role.value}")

    for path, expected in ROLE_EXPECTATIONS[role].items():
        response = client.get(path, follow_redirects=False)
        assert response.status_code == expected, (role.value, path, response.status_code)


def test_a_viewer_cannot_moderate_a_payment(client):
    token = complete_session(client)
    _create(client, "kuzatuvchi", AdminRole.VIEWER)
    _login_as(client, "kuzatuvchi")

    with db_session(client) as db:
        session_id = session_by_token(db, token).id

    response = client.post(f"/admin/personality/{session_id}/grant-premium", follow_redirects=False)
    assert response.status_code == 403
    with db_session(client) as db:
        assert session_by_token(db, token).is_premium is False


# --------------------------------------------------------------------------- hisob holati


def test_a_deactivated_admin_loses_access_immediately(client):
    """Rol cookie'da saqlanmaydi, shuning uchun o'chirish darhol kuchga kiradi."""
    user_id = _create(client, "vaqtinchalik", AdminRole.MODERATOR)
    _login_as(client, "vaqtinchalik")
    assert client.get("/admin/sessions").status_code == 200

    with db_session(client) as db:
        db.get(AdminUser, user_id).is_active = False
        db.commit()

    blocked = client.get("/admin/sessions", follow_redirects=False)
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/admin/login"


def test_a_downgraded_admin_loses_moderation_immediately(client):
    user_id = _create(client, "pasaytiriladi", AdminRole.MODERATOR)
    _login_as(client, "pasaytiriladi")
    assert client.get("/admin/premium-requests").status_code == 200

    with db_session(client) as db:
        db.get(AdminUser, user_id).role = AdminRole.VIEWER.value
        db.commit()

    assert client.get("/admin/premium-requests", follow_redirects=False).status_code == 403


def test_the_env_username_cannot_be_taken_by_a_database_account(client):
    """Ikkita "kim hokim" holati bo'lmasligi kerak."""
    with db_session(client) as db:
        result = admin_service.create_user(
            db, username=settings.admin_username, password=PASSWORD, role=AdminRole.OWNER
        )
    assert result.ok is False
    assert ".env" in result.error


def test_a_row_shadowing_the_env_account_blocks_both_paths(client):
    """`.env` hisobi bilan bir xil nomdagi qator o'chirilsa, kirish rad etiladi.

    IKKALA yo'l ham to'silishi kerak: yangi login ham, ALLAQACHON ochiq sessiya ham.
    Aks holda qatorni o'chirish yangi kirishni to'sardi-yu, ochiq turgan cookie
    egasi huquqida qolaverardi.
    """
    # Qator to'g'ridan-to'g'ri repository orqali yaratiladi: xizmat qatlami endi
    # bunday nomni qabul qilmaydi, lekin eski bazada u allaqachon bo'lishi mumkin.
    with db_session(client) as db:
        row = AdminRepository(db).create_user(
            username=settings.admin_username,
            password_hash=hash_password(PASSWORD),
            role=AdminRole.OWNER,
        )
        row.is_active = False
        db.commit()

    denied = client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert denied.status_code == 401

    with db_session(client) as db:
        identity = admin_service.resolve_web_identity(db, user_id=None, username=settings.admin_username)
    assert identity is None


def test_a_corrupted_session_user_id_is_rejected_not_coerced(client):
    """Buzilgan qiymatni None ga aylantirish `.env` egasi tarmog'iga tushirib yuborardi."""
    admin_login(client)
    payload = {
        "admin_authenticated": True,
        "admin_user_id": "1",
        "admin_username": settings.admin_username,
        "admin_login_at": datetime.now(timezone.utc).timestamp(),
    }
    signer = TimestampSigner(str(settings.secret_key))
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    client.cookies.clear()
    client.cookies.set("session", signer.sign(encoded).decode())

    blocked = client.get("/admin", follow_redirects=False)
    assert blocked.status_code == 303


def test_password_is_verified_exactly_once_per_attempt(client, monkeypatch):
    """Aks holda javob vaqti "bunday login bor" va "yo'q" ni ajratib berardi."""
    calls = []
    original = admin_service.verify_password

    def counting(password, password_hash):
        calls.append(password_hash)
        return original(password, password_hash)

    monkeypatch.setattr(admin_service, "verify_password", counting)
    _create(client, "mavjud", AdminRole.VIEWER)

    for username in ("mavjud", "umuman-yoq", settings.admin_username):
        calls.clear()
        client.post("/admin/login", data={"username": username, "password": "xato-parol"})
        assert len(calls) == 1, (username, len(calls))


def test_a_row_without_a_password_hash_is_rejected_not_crashed(client):
    user_id = _create(client, "hashsiz", AdminRole.VIEWER)
    with db_session(client) as db:
        db.get(AdminUser, user_id).password_hash = ""
        db.commit()

    response = client.post("/admin/login", data={"username": "hashsiz", "password": PASSWORD})
    assert response.status_code == 401


def test_usernames_are_case_insensitive(client):
    _create(client, "erkin", AdminRole.OWNER)
    _login_as(client, "erkin")
    client.get("/admin/logout")

    upper = client.post(
        "/admin/login", data={"username": "ERKIN", "password": PASSWORD}, follow_redirects=False
    )
    assert upper.status_code == 303

    with db_session(client) as db:
        duplicate = admin_service.create_user(db, username="Erkin", password=PASSWORD, role=AdminRole.VIEWER)
    assert duplicate.ok is False


# --------------------------------------------------------------------------- lockout himoyasi


def test_the_last_active_owner_cannot_be_removed(client):
    owner_id = _create(client, "yagona-ega", AdminRole.OWNER)
    with db_session(client) as db:
        user = db.get(AdminUser, owner_id)
        actor = admin_service.identity_from_user(user)

        deactivate = admin_service.set_active(db, user, False, actor=admin_service.env_identity())
        assert deactivate.ok is False
        assert "ega" in deactivate.error

        downgrade = admin_service.set_role(db, user, AdminRole.VIEWER, actor=admin_service.env_identity())
        assert downgrade.ok is False

        self_off = admin_service.set_active(db, user, False, actor=actor)
        assert self_off.ok is False
        assert db.get(AdminUser, owner_id).is_active is True


def test_a_weak_password_is_refused_for_database_accounts(client):
    """Bazadagi hisob ham `.env` hisobi bilan bir xil talabdan o'tadi."""
    with db_session(client) as db:
        result = admin_service.create_user(db, username="zaif", password="admin", role=AdminRole.VIEWER)
    assert result.ok is False
    assert "oson" in result.error.lower() or "belgidan" in result.error


# --------------------------------------------------------------------------- audit


def test_moderation_writes_an_audit_row_with_the_real_actor(client):
    token = complete_session(client)
    _create(client, "moderator1", AdminRole.MODERATOR)
    _login_as(client, "moderator1")

    with db_session(client) as db:
        session_id = session_by_token(db, token).id
    assert client.post(f"/admin/personality/{session_id}/grant-premium").status_code == 200

    with db_session(client) as db:
        entry = db.scalar(
            select(AdminAuditLog).where(AdminAuditLog.action == "manual_premium_granted")
        )
        assert entry is not None
        assert entry.actor_label == "moderator1"
        assert entry.target_type == "session"
        assert entry.target_id == session_id


def test_a_failed_login_is_recorded(client):
    client.post("/admin/login", data={"username": "bosqinchi", "password": "xato"})
    with db_session(client) as db:
        entry = db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "login_failed"))
    assert entry is not None
    assert "bosqinchi" in (entry.detail or "")


def test_the_audit_log_never_stores_a_capability(client):
    """Token, to'lov kodi va chek identifikatori — bularning har biri kirish huquqi."""
    token = complete_session(client)
    admin_login(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session_id, payment_code, share_code = session.id, session.payment_code, session.share_code

    client.post(f"/admin/personality/{session_id}/grant-premium")
    client.get(f"/admin/sessions?code={payment_code}")
    client.get("/admin/export/sessions.csv")

    with db_session(client) as db:
        details = " ".join(row.detail or "" for row in db.scalars(select(AdminAuditLog)).all())
    for secret in (token, payment_code, share_code):
        assert secret and secret not in details

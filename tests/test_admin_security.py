import base64
import json
from datetime import datetime, timezone

from itsdangerous import TimestampSigner

from app.config import settings
from app.personality.themes import PERSONALITY_SESSION_COOKIE_KEY
from app.routers import admin
from app.services.admin_analytics_service import tashkent_day_start
from tests.helpers import admin_login

PUBLIC_ADMIN_PATHS = {"/admin/login", "/admin/logout"}


def _login(client):
    return admin_login(client)


def _session_payload(cookie: str) -> dict:
    unsigned = TimestampSigner(str(settings.secret_key)).unsign(cookie)
    return json.loads(base64.b64decode(unsigned))


def test_every_admin_route_requires_login(client):
    from app.main import app

    checked = 0
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/admin") or path in PUBLIC_ADMIN_PATHS:
            continue
        url = path.replace("{session_id}", "1").replace("{payment_id}", "1")
        for method in sorted(set(getattr(route, "methods", set())) - {"HEAD", "OPTIONS"}):
            response = client.request(method, url, follow_redirects=False)
            assert response.status_code == 303, (method, path, response.status_code)
            assert response.headers["location"] == "/admin/login", (method, path)
            checked += 1
    assert checked >= 8


def test_login_page_and_logout_stay_public(client):
    assert client.get("/admin/login").status_code == 200
    logout = client.get("/admin/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/admin/login"


def test_login_starts_a_clean_session(client):
    client.get("/personality")
    assert PERSONALITY_SESSION_COOKIE_KEY in _session_payload(client.cookies.get("session"))

    _login(client)

    # Session fixation: kirishdan oldingi hamma narsa o'chadi.
    payload = _session_payload(client.cookies.get("session"))
    assert PERSONALITY_SESSION_COOKIE_KEY not in payload
    assert payload["admin_authenticated"] is True
    # Cookie'da faqat shaxs saqlanadi; rol har so'rovda bazadan o'qiladi, aks holda
    # rolni pasaytirish ochiq sessiyaga ta'sir qilmasdi.
    assert payload["admin_username"] == settings.admin_username
    assert "admin_role" not in payload
    assert client.get("/admin").status_code == 200


def test_a_session_without_an_identity_is_rejected(client):
    """Deploy paytida ochiq qolgan eski cookie'da faqat bayroq bo'ladi.

    Uni "hamma narsaga ruxsat" deb qabul qilish huquq oshirishga olib kelardi.
    """
    _login(client)
    signer = TimestampSigner(str(settings.secret_key))
    legacy = base64.b64encode(json.dumps({"admin_authenticated": True}).encode()).decode()
    client.cookies.clear()
    client.cookies.set("session", signer.sign(legacy).decode())

    blocked = client.get("/admin", follow_redirects=False)
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/admin/login"


def test_an_expired_session_is_rejected(client, monkeypatch):
    """SESSION_MAX_AGE mutlaq chegara bo'lishi kerak.

    Starlette cookie'ni har javobda qayta imzolaydi, ya'ni o'g'irlangan cookie
    ishlatilib turilsa muddati hech qachon tugamasdi.
    """
    _login(client)
    assert client.get("/admin").status_code == 200

    monkeypatch.setattr(settings, "session_max_age", 0)
    blocked = client.get("/admin", follow_redirects=False)
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/admin/login"


def test_logout_revokes_access(client):
    _login(client)
    assert client.get("/admin/sessions").status_code == 200

    client.get("/admin/logout")
    blocked = client.get("/admin/sessions", follow_redirects=False)
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/admin/login"


def test_wrong_password_returns_401(client):
    response = client.post(
        "/admin/login",
        data={"username": settings.admin_username, "password": "noto‘g‘ri-parol"},
    )
    assert response.status_code == 401
    assert "noto‘g‘ri" in response.text


def test_login_rate_limit_blocks_brute_force(client):
    enabled_before = admin.login_limiter.enabled
    admin.login_limiter.enabled = True
    try:
        for _ in range(5):
            attempt = client.post("/admin/login", data={"username": "x", "password": "y"})
            assert attempt.status_code == 401
        blocked = client.post("/admin/login", data={"username": "x", "password": "y"})
    finally:
        admin.login_limiter.enabled = enabled_before
    assert blocked.status_code == 429
    assert blocked.json()["detail"]


def test_admin_sessions_pagination(client):
    client.get("/personality?source=direct")
    _login(client)

    first = client.get("/admin/sessions?page=1")
    assert first.status_code == 200
    assert "direct" in first.text

    empty = client.get("/admin/sessions?page=2")
    assert empty.status_code == 200
    assert "direct" not in empty.text

    assert client.get("/admin/sessions?page=0").status_code == 422


def test_premium_requests_page_opens(client):
    _login(client)
    response = client.get("/admin/premium-requests?page=1")
    assert response.status_code == 200


def test_receipt_endpoint_without_bot_token(client, monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "")
    _login(client)
    response = client.get("/admin/premium-requests/1/receipt")
    assert response.status_code == 404
    assert "BOT_TOKEN" in response.json()["detail"]


def test_security_headers_on_every_response(client):
    response = client.get("/personality")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in response.headers
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    # DEBUG=true (secure_cookies o'chiq) da HSTS yuborilmaydi.
    assert "strict-transport-security" not in response.headers


class _FakeTelegramResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, *_args) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False


def _fake_get_file(monkeypatch, payload: dict) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    monkeypatch.setattr(admin, "urlopen", lambda *_a, **_k: _FakeTelegramResponse(encoded))


def test_telegram_file_path_accepts_relative_path(monkeypatch):
    _fake_get_file(monkeypatch, {"ok": True, "result": {"file_path": "photos/file_1.jpg"}})
    assert admin._telegram_file_path("token", "file-id") == "photos/file_1.jpg"


def test_telegram_file_path_rejects_escaping_path(monkeypatch):
    _fake_get_file(monkeypatch, {"ok": True, "result": {"file_path": "../../secret"}})
    assert admin._telegram_file_path("token", "file-id") is None


def test_telegram_file_path_handles_api_error(monkeypatch):
    _fake_get_file(monkeypatch, {"ok": False, "description": "Bad Request"})
    assert admin._telegram_file_path("token", "file-id") is None


def test_error_response_falls_back_to_plain_html(client):
    from starlette.requests import Request

    from app.main import app, error_response

    def _request(accept: str) -> Request:
        return Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/xato",
                "query_string": b"",
                "headers": [(b"accept", accept.encode())],
                "app": app,
                "router": app.router,
            }
        )

    html = error_response(_request("text/html"), 500)
    assert html.status_code == 500
    assert html.headers["content-type"].startswith("text/html")

    api = error_response(_request("application/json"), 500)
    assert api.status_code == 500
    assert api.headers["content-type"].startswith("application/json")


def test_missing_page_renders_html_for_browsers(client):
    html = client.get("/bunday-sahifa-yoq", headers={"accept": "text/html"})
    assert html.status_code == 404
    assert html.headers["content-type"].startswith("text/html")
    assert "Sahifa topilmadi" in html.text
    assert "Not Found" not in html.text

    api = client.get("/bunday-sahifa-yoq", headers={"accept": "application/json"})
    assert api.status_code == 404
    assert api.json()["detail"] == "So‘ralgan sahifa mavjud emas yoki ko‘chirilgan."


def test_tashkent_day_start_is_utc_plus_five():
    moment = datetime(2026, 8, 6, 20, 30, tzinfo=timezone.utc)  # Toshkentda 7-avgust 01:30
    assert tashkent_day_start(moment) == datetime(2026, 8, 6, 19, 0, tzinfo=timezone.utc)

    before_midnight = datetime(2026, 8, 6, 18, 59, tzinfo=timezone.utc)  # Toshkentda 23:59
    assert tashkent_day_start(before_midnight) == datetime(2026, 8, 5, 19, 0, tzinfo=timezone.utc)

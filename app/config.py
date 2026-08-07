from __future__ import annotations

import logging
import secrets

from passlib.context import CryptContext
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# passlib 1.7.4 bcrypt >= 4.1 dan versiya raqamini o'qiy olmaydi va har chaqiruvda
# tracebackli ogohlantirish yozadi. Xatoning o'zi zararsiz, shuning uchun shu logger jimlatiladi.
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PLACEHOLDER_SECRET_KEYS = frozenset(
    {
        "dev-secret-key",
        "change-me-in-production",
        "changeme",
        "secret",
        "your-secret-key",
    }
)
LOCAL_URL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0")

# Shablonlar faqat /static dan foydalanadi (bootstrap va shriftlar self-host qilingan),
# shuning uchun tashqi manbalarga ruxsat yo'q. 'unsafe-inline' faqat style uchun kerak:
# progress chiziqlari inline style atributi bilan chiziladi.
DEFAULT_CSP = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "object-src 'none'; "
    "img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; "
    "script-src 'self'; "
    "connect-src 'self'"
)

DEFAULT_LOG_LEVEL = "INFO"

# Admin paroli uchun eng kam talab — .env dagi hisob ham, bazadagi hisob ham
# shu bir xil qoidadan o'tadi.
MIN_ADMIN_PASSWORD_LENGTH = 10
WEAK_ADMIN_PASSWORDS = frozenset({"admin", "admin123", "password", "parol", "12345678", "qwerty"})

RETENTION_FIELDS = (
    "retention_visited_days",
    "retention_incomplete_days",
    "retention_outbox_days",
    "retention_audit_days",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def admin_credential_problems(username: str, password: str | None, *, debug: bool) -> list[str]:
    """Login/parol siyosati — `.env` tekshiruvi va hisob yaratish uchun bitta manba.

    Aks holda bazadagi hisoblar `.env` hisobidan past talabga tushib qolardi:
    validator import vaqtida faqat `.env` qiymatlarini ko'radi.
    """
    problems: list[str] = []
    cleaned = (username or "").strip()
    if not cleaned:
        problems.append("Login bo'sh bo'lishi mumkin emas")
    elif cleaned.lower() == "admin" and not debug:
        problems.append("Production'da login 'admin' bo'lishi mumkin emas")

    if password is None:
        return problems
    if password.strip().lower() in WEAK_ADMIN_PASSWORDS:
        problems.append("Parol juda oson (taqiqlangan ro'yxatda)")
    elif len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        problems.append(f"Parol kamida {MIN_ADMIN_PASSWORD_LENGTH} belgidan iborat bo'lishi kerak")
    return problems


def verify_password(password: str, password_hash: str | None) -> bool:
    """passlib noto'g'ri formatdagi hash uchun ValueError otadi; uni False deb qaraymiz."""
    if not password_hash:
        # Hash yo'q (masalan hali faollashtirilmagan hisob): passlib None uchun
        # TypeError otardi va login 500 bilan yiqilardi.
        return False
    try:
        return pwd_context.verify(password, password_hash)
    except ValueError:
        return False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./mbti_dev.db"
    secret_key: str = ""
    debug: bool = True

    admin_username: str = "admin"
    admin_password: str = ""
    admin_password_hash: str = ""
    # false bo'lsa `.env` dagi zaxira hisob bilan kirish o'chiriladi va hisoblar
    # faqat bazada bo'ladi. Shunda `.env` dagi ADMIN_* qiymatlari talab qilinmaydi.
    admin_env_login_enabled: bool = True

    bot_username: str = ""
    bot_token: str = ""
    premium_price: int = 9990
    # Savol to'plamlari taqsimoti: "A" yoki vaznli "A:70,B:30".
    question_variants: str = "A"
    payment_card_number: str = ""
    payment_card_holder: str = ""
    payment_support_bot_username: str = ""
    admin_telegram_id: int | None = None
    # Vergul bilan ajratilgan ro'yxat. `list[int]` deb e'lon qilinsa pydantic-settings
    # qiymatni JSON deb o'qiydi va "111,222" import vaqtida SettingsError beradi —
    # shuning uchun trusted_proxies bilan bir xil naqsh ishlatiladi.
    admin_telegram_ids: str = ""
    public_base_url: str = "http://127.0.0.1:8000"

    # --- Bildirishnoma navbati ---
    outbox_max_attempts: int = 8
    outbox_poll_seconds: int = 5
    outbox_batch_size: int = 5
    # Ishchi qatorni shu muddatga "ijaraga oladi"; jarayon o'lsa qator shundan keyin
    # qaytadan olinadi.
    outbox_lease_seconds: int = 180
    # Shu vaqtdan uzoq kutgan qator admin sahifasida ogohlantirish sifatida ko'rinadi.
    outbox_overdue_minutes: int = 15

    # --- Eksport ---
    export_max_rows: int = 50_000

    # --- Ma'lumotlarni saqlash muddati (kun; 0 = qoida o'chirilgan) ---
    retention_visited_days: int = 30
    retention_incomplete_days: int = 90
    retention_outbox_days: int = 30
    retention_audit_days: int = 730

    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.0
    log_level: str = DEFAULT_LOG_LEVEL
    # uvicorn access log konkret yo'lni (va natija tokenini) yozadi, shuning uchun o'chiq.
    access_log: bool = False

    rate_limit_enabled: bool = True
    rate_limit_login: str = "5/minute"
    rate_limit_storage_uri: str = "memory://"

    # None bo'lsa DEBUG bo'yicha aniqlanadi: productionʼda yoqiq, lokalda o'chiq.
    secure_cookies: bool | None = None
    # 14 kunlik sessiya admin panel uchun juda uzun: o'g'irlangan cookie shuncha vaqt ishlaydi.
    session_max_age: int = 8 * 60 * 60
    trusted_proxies: str = "127.0.0.1"
    content_security_policy: str = DEFAULT_CSP

    @field_validator("secure_cookies", mode="before")
    @classmethod
    def _blank_secure_cookies_is_auto(cls, value: object) -> object:
        # .env da `SECURE_COOKIES=` qolib ketsa sozlama "avtomatik" holatda qolsin.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("content_security_policy", mode="before")
    @classmethod
    def _blank_csp_is_default(cls, value: object) -> object:
        # Bo'sh CSP butun siyosatni jimgina o'chirib qo'yardi — standartga qaytamiz.
        if isinstance(value, str) and not value.strip():
            return DEFAULT_CSP
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _blank_log_level_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_LOG_LEVEL
        return value

    @property
    def secure_cookies_enabled(self) -> bool:
        if self.secure_cookies is None:
            return not self.debug
        return self.secure_cookies

    @field_validator(*RETENTION_FIELDS, mode="after")
    @classmethod
    def _no_negative_retention(cls, value: int) -> int:
        # Manfiy qiymat "kesish chegarasi = hozir" degani bo'lib, butun jadvalni
        # o'chirib yuborardi. 0 esa ataylab "qoida o'chirilgan" degani.
        if value < 0:
            raise ValueError("saqlash muddati manfiy bo'lishi mumkin emas (0 = o'chirilgan)")
        return value

    @property
    def trusted_proxy_hosts(self) -> list[str]:
        return [host.strip() for host in self.trusted_proxies.split(",") if host.strip()]

    @property
    def admin_telegram_id_set(self) -> frozenset[int]:
        """ADMIN_TELEGRAM_IDS + eski ADMIN_TELEGRAM_ID birlashmasi."""
        ids: set[int] = set()
        if self.admin_telegram_id:
            ids.add(int(self.admin_telegram_id))
        for chunk in self.admin_telegram_ids.split(","):
            cleaned = chunk.strip()
            if not cleaned:
                continue
            try:
                ids.add(int(cleaned))
            except ValueError:
                logger.warning("ADMIN_TELEGRAM_IDS dagi qiymat raqam emas, o'tkazib yuborildi")
        return frozenset(ids)

    def retention_days(self, rule: str) -> int | None:
        """Qoida uchun kun soni; 0 bo'lsa None (ya'ni qoida bajarilmaydi)."""
        value = int(getattr(self, f"retention_{rule}_days"))
        return value or None

    @property
    def secret_key_is_weak(self) -> bool:
        value = self.secret_key.strip()
        return not value or value in PLACEHOLDER_SECRET_KEYS

    @property
    def public_base_url_is_local(self) -> bool:
        value = self.public_base_url.strip().lower()
        return any(host in value for host in LOCAL_URL_HOSTS)

    @model_validator(mode="after")
    def _enforce_security(self) -> Settings:
        problems: list[str] = []

        if self.secret_key_is_weak:
            problems.append(
                "SECRET_KEY berilmagan yoki namunaviy qiymatda; "
                '`python -c "import secrets; print(secrets.token_urlsafe(48))"` bilan yangisini yarating'
            )

        if self.admin_env_login_enabled:
            if self.admin_password == "admin":
                problems.append("ADMIN_PASSWORD sifatida 'admin' ishlatilmoqda")

            if self.admin_username == "admin" and not self.debug:
                problems.append("Production'da ADMIN_USERNAME 'admin' bo'lishi mumkin emas")

        if self.public_base_url_is_local and not self.debug:
            problems.append(
                "DEBUG=false bo'lganda PUBLIC_BASE_URL lokal manzil bo'lishi mumkin emas: "
                f"{self.public_base_url}"
            )

        if not self.admin_env_login_enabled:
            # Hisoblar faqat bazada: `.env` dagi ADMIN_* talab qilinmaydi.
            pass
        elif not self.admin_password_hash:
            if not self.admin_password:
                problems.append(
                    "ADMIN_PASSWORD_HASH ham, ADMIN_PASSWORD ham berilmagan, admin panelga kirib bo'lmaydi"
                )
            elif self.debug:
                # Lokal qulaylik: ochiq parol bir marta, ishga tushishda hashlanadi.
                self.admin_password_hash = hash_password(self.admin_password)
                logger.warning(
                    "ADMIN_PASSWORD_HASH berilmagan, ADMIN_PASSWORD ishga tushishda hashlandi. "
                    "Production uchun ADMIN_PASSWORD_HASH ni .env ga yozing."
                )
            else:
                problems.append(
                    "DEBUG=false bo'lganda ochiq ADMIN_PASSWORD emas, ADMIN_PASSWORD_HASH talab qilinadi"
                )

        if not problems:
            return self

        if not self.debug:
            raise RuntimeError("Xavfsiz bo'lmagan sozlamalar: " + "; ".join(problems))

        for problem in problems:
            logger.warning("Xavfsizlik ogohlantirishi (DEBUG=true): %s", problem)
        if self.secret_key_is_weak:
            # Lokalda sessiya imzosi ishlashi uchun vaqtinchalik kalit; har qayta ishga tushganda yangilanadi.
            self.secret_key = secrets.token_urlsafe(48)
        return self


settings = Settings()

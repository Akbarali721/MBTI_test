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


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """passlib noto'g'ri formatdagi hash uchun ValueError otadi; uni False deb qaraymiz."""
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

    bot_username: str = ""
    bot_token: str = ""
    premium_price: int = 9990
    # Savol to'plamlari taqsimoti: "A" yoki vaznli "A:70,B:30".
    question_variants: str = "A"
    payment_card_number: str = ""
    payment_card_holder: str = ""
    payment_support_bot_username: str = ""
    admin_telegram_id: int | None = None
    public_base_url: str = "http://127.0.0.1:8000"

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

    @property
    def trusted_proxy_hosts(self) -> list[str]:
        return [host.strip() for host in self.trusted_proxies.split(",") if host.strip()]

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

        if self.admin_password == "admin":
            problems.append("ADMIN_PASSWORD sifatida 'admin' ishlatilmoqda")

        if self.admin_username == "admin" and not self.debug:
            problems.append("Production'da ADMIN_USERNAME 'admin' bo'lishi mumkin emas")

        if self.public_base_url_is_local and not self.debug:
            problems.append(
                "DEBUG=false bo'lganda PUBLIC_BASE_URL lokal manzil bo'lishi mumkin emas: "
                f"{self.public_base_url}"
            )

        if not self.admin_password_hash:
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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./mbti_dev.db"
    secret_key: str = "dev-secret-key"
    admin_username: str = "admin"
    admin_password: str = "admin"
    debug: bool = True

    bot_username: str = ""
    bot_token: str = ""
    premium_price: int = 9990
    payment_card_number: str = ""
    payment_card_holder: str = ""
    payment_admin_telegram: str = ""
    payment_support_bot_username: str = "xarakter_test_support_bot"
    admin_telegram_id: int | None = None
    public_base_url: str = "http://127.0.0.1:8000"


settings = Settings()

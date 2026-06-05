from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env into os.environ before Settings is constructed.
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "South East Archers"
    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "FLASK_ENV"))
    app_debug: bool = False
    app_url: str = "http://127.0.0.1:8000"

    secret_key: str = Field(default="dev-key-change-in-production")
    database_url: str = Field(
        default="mysql+pymysql://sea_user:sea_password@localhost:3306/sea_db",
        validation_alias="DATABASE_URL",
    )

    session_max_age_seconds: int = 7 * 24 * 60 * 60
    session_secure_cookie: bool = True

    mail_server: str = "localhost"
    mail_port: int = 587
    mail_use_tls: bool = True
    mail_use_ssl: bool = False
    mail_username: str | None = None
    mail_password: str | None = None
    mail_default_sender: str = "noreply@southeastarchers.ie"

    payment_processor: str = "sumup"
    sumup_api_key: str | None = None
    sumup_merchant_code: str | None = None
    sumup_api_url: str = "https://api.sumup.com"

    recaptcha_public_key: str | None = Field(default=None, validation_alias="RECAPTCHA_PUBLIC_KEY")
    recaptcha_private_key: str | None = Field(default=None, validation_alias="RECAPTCHA_PRIVATE_KEY")

    vite_dev_server_url: str = "http://localhost:5173"

    def model_post_init(self, __context: object) -> None:
        if self.is_development:
            object.__setattr__(self, "app_debug", True)
            object.__setattr__(self, "session_secure_cookie", False)
        if self.is_testing:
            object.__setattr__(self, "session_secure_cookie", False)

    @property
    def is_mysql(self) -> bool:
        return self.database_url.startswith("mysql")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production:
        missing = []
        if settings.secret_key == "dev-key-change-in-production":
            missing.append("SECRET_KEY")
        if not settings.mail_server:
            missing.append("MAIL_SERVER")
        if not settings.is_mysql:
            missing.append("DATABASE_URL")
        if missing:
            raise RuntimeError(f"Required configuration missing for production: {', '.join(missing)}")
    return settings

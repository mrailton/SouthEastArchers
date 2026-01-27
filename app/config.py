import os
from datetime import timedelta


def _get_bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name, str(default)).lower()
    return val in ("true", "1", "yes", "on")


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "mysql+pymysql://sea_user:sea_password@localhost:3306/sea_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = _get_bool_env("SESSION_COOKIE_SECURE", True)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Security Headers
    TALISMAN_ENABLED = _get_bool_env("TALISMAN_ENABLED", True)

    # Email
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _get_bool_env("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _get_bool_env("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@southeastarchers.ie")
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = False

    # Payment
    PAYMENT_PROCESSOR = os.environ.get("PAYMENT_PROCESSOR", "sumup")  # Default processor
    SUMUP_API_KEY = os.environ.get("SUMUP_API_KEY")
    SUMUP_MERCHANT_CODE = os.environ.get("SUMUP_MERCHANT_CODE")
    SUMUP_API_URL = "https://api.sumup.com"

    # Membership (prices in cents to avoid floating point issues)
    ANNUAL_MEMBERSHIP_COST = 10000  # 100.00 EUR (stored as cents)
    MEMBERSHIP_NIGHTS_INCLUDED = 20
    ADDITIONAL_NIGHT_COST = 500  # 5.00 EUR per night (stored as cents)


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    JINJA_AUTO_RELOAD = True
    SESSION_COOKIE_SECURE = False
    TALISMAN_ENABLED = False
    MAIL_USE_TLS = False
    SERVER_NAME = os.environ.get("SERVER_NAME", "localhost:5000")
    PREFERRED_URL_SCHEME = "http"


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    PREFERRED_URL_SCHEME = "http"
    BCRYPT_LOG_ROUNDS = 4  # Minimum rounds for fast tests (default is 12)


class ProductionConfig(Config):
    """Production configuration"""

    pass


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

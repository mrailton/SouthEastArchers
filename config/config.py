import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    DEBUG = False
    TESTING = False

    # Server configuration for URL generation outside request context
    SERVER_NAME = os.environ.get("SERVER_NAME")  # e.g., "southeastarchers.ie"
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT", "/")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://sea_user:sea_password@localhost:3306/sea_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Email
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    # Force proper boolean conversion for TLS/SSL settings
    mail_use_tls = os.environ.get("MAIL_USE_TLS", "True")
    MAIL_USE_TLS = mail_use_tls.lower() in ("true", "1", "yes", "on") if isinstance(mail_use_tls, str) else bool(mail_use_tls)
    mail_use_ssl = os.environ.get("MAIL_USE_SSL", "False")
    MAIL_USE_SSL = mail_use_ssl.lower() in ("true", "1", "yes", "on") if isinstance(mail_use_ssl, str) else bool(mail_use_ssl)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@southeastarchers.ie"
    )
    # Additional mail settings for better compatibility
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

    # Redis & Background Jobs
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    JINJA_AUTO_RELOAD = True
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_ECHO = False
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    SERVER_NAME = os.environ.get("SERVER_NAME", "localhost:5000")
    PREFERRED_URL_SCHEME = "http"


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SERVER_NAME = "localhost.localdomain"
    PREFERRED_URL_SCHEME = "http"
    BCRYPT_LOG_ROUNDS = 4  # Minimum rounds for fast tests (default is 12)


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

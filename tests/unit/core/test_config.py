import pytest

from app.core.config import Settings, get_settings


def test_settings_is_mysql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost/db")
    settings = Settings()
    assert settings.is_mysql is True


def test_settings_development_flags(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    settings = Settings()
    assert settings.app_debug is True
    assert settings.session_secure_cookie is False


def test_production_missing_config_raises(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "dev-key-change-in-production")
    monkeypatch.delenv("MAIL_SERVER", raising=False)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="Required configuration missing"):
        get_settings()
    get_settings.cache_clear()

import logging
from unittest.mock import patch

from app.main import _configure_app_logging, _session_user_for_error_page
from app.templating import AnonymousUser


def test_session_user_for_error_page_returns_anonymous_when_db_fails():
    request = type("Request", (), {"session": {"user_id": 1}})()

    with patch("app.main._session_user", side_effect=RuntimeError("db down")):
        user = _session_user_for_error_page(request)

    assert isinstance(user, AnonymousUser)
    assert user.is_authenticated is False


def test_session_user_for_error_page_returns_anonymous_when_logged_out():
    request = type("Request", (), {"session": {}})()
    user = _session_user_for_error_page(request)
    assert isinstance(user, AnonymousUser)


def test_unknown_route_returns_404_not_500(client):
    """Hitting an unmapped URL must render the 404 page, not cascade into a 500."""
    response = client.get("/this-route-does-not-exist-xyz")
    assert response.status_code == 404


def test_configure_app_logging_adds_handler_outside_tests():
    """_configure_app_logging must attach a StreamHandler when not in test mode."""
    app_logger = logging.getLogger("app")
    original_handlers = app_logger.handlers[:]
    original_propagate = app_logger.propagate

    try:
        app_logger.handlers.clear()
        with patch("app.main.settings") as mock_settings:
            mock_settings.is_testing = False
            mock_settings.log_level = "DEBUG"
            _configure_app_logging()

        assert any(isinstance(h, logging.StreamHandler) for h in app_logger.handlers)
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.handlers = original_handlers
        app_logger.propagate = original_propagate


def test_configure_app_logging_skips_handler_when_already_present():
    """A second call must not add a duplicate handler."""
    app_logger = logging.getLogger("app")
    original_handlers = app_logger.handlers[:]

    try:
        existing = logging.StreamHandler()
        app_logger.handlers = [existing]
        with patch("app.main.settings") as mock_settings:
            mock_settings.is_testing = False
            mock_settings.log_level = "INFO"
            _configure_app_logging()

        assert app_logger.handlers == [existing]
    finally:
        app_logger.handlers = original_handlers

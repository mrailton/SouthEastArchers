from unittest.mock import patch

from app.main import _session_user_for_error_page
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

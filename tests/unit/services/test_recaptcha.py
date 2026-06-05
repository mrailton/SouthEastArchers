import asyncio
from unittest.mock import AsyncMock, Mock, patch

from app.services import recaptcha


def test_verify_recaptcha_testing_env_returns_true(app):
    assert asyncio.run(recaptcha.verify_recaptcha("")) is True


def test_verify_recaptcha_no_key_debug_mode():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="", app_debug=True)
    with patch("app.services.recaptcha.get_settings", return_value=mock_settings):
        assert asyncio.run(recaptcha.verify_recaptcha("token")) is True


def test_verify_recaptcha_empty_token_production():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="secret", app_debug=False)
    with patch("app.services.recaptcha.get_settings", return_value=mock_settings):
        assert asyncio.run(recaptcha.verify_recaptcha("")) is False


def test_verify_recaptcha_http_success():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="secret", app_debug=False)
    mock_response = Mock()
    mock_response.json.return_value = {"success": True}
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with (
        patch("app.services.recaptcha.get_settings", return_value=mock_settings),
        patch("app.services.recaptcha.httpx.AsyncClient", return_value=mock_client),
    ):
        assert asyncio.run(recaptcha.verify_recaptcha("valid-token")) is True

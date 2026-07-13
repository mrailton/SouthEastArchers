from unittest.mock import MagicMock, Mock, patch

from app.services import recaptcha


def test_verify_recaptcha_testing_env_returns_true(app):
    assert recaptcha.verify_recaptcha("") is True


def test_verify_recaptcha_no_key_debug_mode():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="", app_debug=True)
    with patch("app.services.recaptcha.get_settings", return_value=mock_settings):
        assert recaptcha.verify_recaptcha("token") is True


def test_verify_recaptcha_empty_token_production():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="secret", app_debug=False)
    with patch("app.services.recaptcha.get_settings", return_value=mock_settings):
        assert recaptcha.verify_recaptcha("") is False


def test_verify_recaptcha_http_success():
    mock_settings = Mock(is_testing=False, recaptcha_private_key="secret", app_debug=False)
    mock_response = Mock()
    mock_response.json.return_value = {"success": True}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    with (
        patch("app.services.recaptcha.get_settings", return_value=mock_settings),
        patch("app.services.recaptcha.httpx.Client", return_value=mock_client),
    ):
        assert recaptcha.verify_recaptcha("valid-token") is True

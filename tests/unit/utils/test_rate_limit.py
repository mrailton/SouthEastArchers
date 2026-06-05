from unittest.mock import Mock, patch

from app.utils import rate_limit


def _request(host: str = "203.0.113.10"):
    return Mock(client=Mock(host=host))


def test_check_rate_limit_allows_under_threshold():
    rate_limit.clear_rate_limits()
    req = _request()
    assert rate_limit.check_rate_limit(req, "test:scope", max_attempts=3, window_seconds=60) is False
    assert rate_limit.check_rate_limit(req, "test:scope", max_attempts=3, window_seconds=60) is False
    assert rate_limit.check_rate_limit(req, "test:scope", max_attempts=3, window_seconds=60) is False


def test_check_rate_limit_blocks_over_threshold():
    rate_limit.clear_rate_limits()
    req = _request("203.0.113.11")
    for _ in range(3):
        rate_limit.check_rate_limit(req, "test:block", max_attempts=3, window_seconds=60)
    assert rate_limit.check_rate_limit(req, "test:block", max_attempts=3, window_seconds=60) is True


def test_testing_env_ignores_redis_url_even_when_configured():
    rate_limit.clear_rate_limits()
    mock_settings = Mock(is_testing=True, redis_url="redis://localhost:6379/0")
    req = _request("203.0.113.12")
    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        assert rate_limit.check_rate_limit(req, "test:no-redis", max_attempts=5, window_seconds=60) is False


def test_check_rate_limit_uses_redis_when_available():
    rate_limit.clear_rate_limits()
    mock_redis = Mock()
    mock_redis.incr.return_value = 1
    mock_settings = Mock(is_testing=False, redis_url="redis://localhost:6379/0")
    req = _request("203.0.113.20")

    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        with patch("redis.Redis.from_url", return_value=mock_redis):
            assert rate_limit.check_rate_limit(req, "redis:ok", max_attempts=5, window_seconds=60) is False

    mock_redis.incr.assert_called_once()
    mock_redis.expire.assert_called_once()


def test_check_rate_limit_redis_blocks_when_over_threshold():
    rate_limit.clear_rate_limits()
    mock_redis = Mock()
    mock_redis.incr.return_value = 6
    mock_settings = Mock(is_testing=False, redis_url="redis://localhost:6379/0")
    req = _request("203.0.113.21")

    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        with patch("redis.Redis.from_url", return_value=mock_redis):
            assert rate_limit.check_rate_limit(req, "redis:block", max_attempts=5, window_seconds=60) is True


def test_get_redis_marks_unavailable_after_connection_failure():
    rate_limit.clear_rate_limits()
    mock_settings = Mock(is_testing=False, redis_url="redis://localhost:6379/0")

    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        with patch("redis.Redis.from_url", side_effect=RuntimeError("redis down")):
            assert rate_limit._get_redis() is None
            assert rate_limit._get_redis() is None


def test_get_redis_returns_none_without_url():
    rate_limit.clear_rate_limits()
    mock_settings = Mock(is_testing=False, redis_url=None)
    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        assert rate_limit._get_redis() is None


def test_get_redis_reuses_cached_client():
    rate_limit.clear_rate_limits()
    mock_redis = Mock()
    mock_settings = Mock(is_testing=False, redis_url="redis://localhost:6379/0")
    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        with patch("redis.Redis.from_url", return_value=mock_redis) as from_url:
            assert rate_limit._get_redis() is mock_redis
            assert rate_limit._get_redis() is mock_redis
            from_url.assert_called_once()


def test_check_rate_limit_falls_back_when_redis_incr_fails():
    rate_limit.clear_rate_limits()
    mock_redis = Mock()
    mock_redis.incr.side_effect = RuntimeError("incr failed")
    mock_settings = Mock(is_testing=False, redis_url="redis://localhost:6379/0")
    req = _request("203.0.113.22")

    with patch("app.utils.rate_limit.get_settings", return_value=mock_settings):
        with patch("redis.Redis.from_url", return_value=mock_redis):
            assert rate_limit.check_rate_limit(req, "redis:fallback", max_attempts=3, window_seconds=60) is False

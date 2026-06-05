from unittest.mock import Mock, patch

from app.core.config import get_settings
from app.services.sumup import SumUpService


class MockAPIError(Exception):
    pass


def test_init_with_api_key():
    service = SumUpService(api_key="test_key")
    assert service.api_key == "test_key"


def test_init_without_api_key_uses_config(monkeypatch):
    monkeypatch.setenv("SUMUP_API_KEY", "config_key")
    get_settings.cache_clear()
    service = SumUpService()
    assert service.api_key == "config_key"


@patch("app.services.sumup.Sumup")
def test_create_checkout_success(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "TEST_MERCHANT")
    get_settings.cache_clear()

    mock_response = Mock()
    mock_response.id = "checkout_123"
    mock_response.checkout_reference = "ref_123"
    mock_response.status = "PENDING"

    mock_client = Mock()
    mock_client.checkouts.create.return_value = mock_response
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(
        amount=10000,
        currency="EUR",
        description="Test payment",
        checkout_reference="ref_123",
    )

    assert result is not None
    assert result["id"] == "checkout_123"
    assert result["checkout_reference"] == "ref_123"
    assert result["status"] == "PENDING"


@patch("app.services.sumup.Sumup")
def test_create_checkout_auto_generates_reference(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "TEST_MERCHANT")
    get_settings.cache_clear()

    mock_response = Mock()
    mock_response.id = "checkout_123"
    mock_response.checkout_reference = "auto_ref"
    mock_response.status = "PENDING"

    mock_client = Mock()
    mock_client.checkouts.create.return_value = mock_response
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=5000)

    assert result is not None
    assert result["id"] == "checkout_123"


@patch("app.services.sumup.Sumup")
def test_create_checkout_uses_merchant_code_from_config(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "CONFIG_MERCHANT")
    get_settings.cache_clear()

    mock_response = Mock()
    mock_response.id = "checkout_123"
    mock_response.status = "PENDING"

    mock_client = Mock()
    mock_client.checkouts.create.return_value = mock_response
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=10000)

    assert result is not None


@patch("app.services.sumup.Sumup")
def test_create_checkout_no_merchant_code_raises_error(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "")
    get_settings.cache_clear()

    mock_sumup_class.return_value = Mock()
    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=10000)

    assert result is None


@patch("app.services.sumup.APIError", MockAPIError)
@patch("app.services.sumup.Sumup")
def test_create_checkout_api_error(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "TEST_MERCHANT")
    get_settings.cache_clear()

    mock_client = Mock()
    mock_client.checkouts.create.side_effect = MockAPIError("API Error")
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=10000)

    assert result is None


@patch("app.services.sumup.Sumup")
def test_create_checkout_response_without_id(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "TEST_MERCHANT")
    get_settings.cache_clear()

    mock_response = Mock(spec=[])
    mock_client = Mock()
    mock_client.checkouts.create.return_value = mock_response
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=10000)

    assert result is None


@patch("app.services.sumup.Sumup")
def test_create_checkout_generic_exception(mock_sumup_class, monkeypatch):
    monkeypatch.setenv("SUMUP_MERCHANT_CODE", "TEST_MERCHANT")
    get_settings.cache_clear()

    mock_client = Mock()
    mock_client.checkouts.create.side_effect = Exception("Unexpected error")
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.create_checkout(amount=10000)

    assert result is None


@patch("app.services.sumup.Sumup")
def test_get_checkout_success(mock_sumup_class):
    mock_checkout = Mock()
    mock_checkout.id = "checkout_123"
    mock_checkout.status = "PAID"

    mock_client = Mock()
    mock_client.checkouts.get.return_value = mock_checkout
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.get_checkout("checkout_123")

    assert result is not None
    assert result.id == "checkout_123"
    assert result.status == "PAID"


@patch("app.services.sumup.APIError", MockAPIError)
@patch("app.services.sumup.Sumup")
def test_get_checkout_api_error(mock_sumup_class):
    mock_client = Mock()
    mock_client.checkouts.get.side_effect = MockAPIError("Not found")
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.get_checkout("invalid_id")

    assert result is None


@patch("app.services.sumup.Sumup")
def test_get_checkout_generic_exception(mock_sumup_class):
    mock_client = Mock()
    mock_client.checkouts.get.side_effect = Exception("Network error")
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.get_checkout("checkout_123")

    assert result is None


@patch("app.services.sumup.Sumup")
def test_verify_payment_success_paid(mock_sumup_class):
    mock_checkout = Mock()
    mock_checkout.status = "PAID"

    mock_client = Mock()
    mock_client.checkouts.get.return_value = mock_checkout
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("checkout_123")

    assert result is True


@patch("app.services.sumup.Sumup")
def test_verify_payment_not_paid(mock_sumup_class):
    mock_checkout = Mock()
    mock_checkout.status = "PENDING"

    mock_client = Mock()
    mock_client.checkouts.get.return_value = mock_checkout
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("checkout_123")

    assert result is False


@patch("app.services.sumup.Sumup")
def test_verify_payment_checkout_not_found(mock_sumup_class):
    mock_client = Mock()
    mock_client.checkouts.get.return_value = None
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("invalid_id")

    assert result is False


@patch("app.services.sumup.Sumup")
def test_verify_payment_no_status_attribute(mock_sumup_class):
    mock_checkout = Mock(spec=[])

    mock_client = Mock()
    mock_client.checkouts.get.return_value = mock_checkout
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("checkout_123")

    assert result is False


@patch("app.services.sumup.Sumup")
def test_verify_payment_exception(mock_sumup_class):
    mock_client = Mock()
    mock_client.checkouts.get.side_effect = Exception("Error")
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("checkout_123")

    assert result is False


@patch("app.services.sumup.Sumup")
def test_verify_payment_exception_during_check(mock_sumup_class):
    mock_checkout = Mock()
    mock_checkout.status = property(lambda self: (_ for _ in ()).throw(Exception("Status check error")))

    mock_client = Mock()
    mock_client.checkouts.get.return_value = mock_checkout
    mock_sumup_class.return_value = mock_client

    service = SumUpService(api_key="test_key")
    result = service.verify_payment("checkout_123")

    assert result is False

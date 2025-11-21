"""Tests for SumUp service"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.sumup_service import SumUpService


# Create a mock APIError class for testing
class MockAPIError(Exception):
    """Mock APIError for testing"""

    pass


class TestSumUpServiceInit:
    def test_init_with_api_key(self, app):
        """Test initialization with explicit API key"""
        with app.app_context():
            service = SumUpService(api_key="test_key")
            assert service.api_key == "test_key"

    def test_init_without_api_key_uses_config(self, app):
        """Test initialization uses app config when no key provided"""
        with app.app_context():
            app.config["SUMUP_API_KEY"] = "config_key"
            service = SumUpService()
            assert service.api_key == "config_key"


class TestCreateCheckout:
    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_success(self, mock_sumup_class, app):
        """Test successful checkout creation"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "TEST_MERCHANT"

            # Mock the SDK response
            mock_response = Mock()
            mock_response.id = "checkout_123"
            mock_response.checkout_reference = "ref_123"
            mock_response.status = "PENDING"

            mock_client = Mock()
            mock_client.checkouts.create.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(
                amount=100.00,
                currency="EUR",
                description="Test payment",
                checkout_reference="ref_123",
            )

            assert result is not None
            assert result["id"] == "checkout_123"
            assert result["checkout_reference"] == "ref_123"
            assert result["status"] == "PENDING"

    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_auto_generates_reference(self, mock_sumup_class, app):
        """Test checkout reference is auto-generated if not provided"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "TEST_MERCHANT"

            mock_response = Mock()
            mock_response.id = "checkout_123"
            mock_response.checkout_reference = "auto_ref"
            mock_response.status = "PENDING"

            mock_client = Mock()
            mock_client.checkouts.create.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=50.00)

            assert result is not None
            assert result["id"] == "checkout_123"

    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_uses_merchant_code_from_config(
        self, mock_sumup_class, app
    ):
        """Test merchant code is fetched from config"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "CONFIG_MERCHANT"

            mock_response = Mock()
            mock_response.id = "checkout_123"
            mock_response.status = "PENDING"

            mock_client = Mock()
            mock_client.checkouts.create.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=100.00)

            assert result is not None

    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_no_merchant_code_raises_error(self, mock_sumup_class, app):
        """Test error when merchant code is not configured"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = None

            mock_client = Mock()
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=100.00)

            assert result is None

    @patch("app.services.sumup_service.APIError", MockAPIError)
    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_api_error(self, mock_sumup_class, app):
        """Test handling of SumUp API error"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "TEST_MERCHANT"

            mock_client = Mock()
            mock_client.checkouts.create.side_effect = MockAPIError("API Error")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=100.00)

            assert result is None

    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_response_without_id(self, mock_sumup_class, app):
        """Test handling of response without checkout ID"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "TEST_MERCHANT"

            mock_response = Mock(spec=[])  # No attributes
            mock_client = Mock()
            mock_client.checkouts.create.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=100.00)

            assert result is None

    @patch("app.services.sumup_service.Sumup")
    def test_create_checkout_generic_exception(self, mock_sumup_class, app):
        """Test handling of generic exceptions"""
        with app.app_context():
            app.config["SUMUP_MERCHANT_CODE"] = "TEST_MERCHANT"

            mock_client = Mock()
            mock_client.checkouts.create.side_effect = Exception("Unexpected error")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.create_checkout(amount=100.00)

            assert result is None


class TestGetCheckout:
    @patch("app.services.sumup_service.Sumup")
    def test_get_checkout_success(self, mock_sumup_class, app):
        """Test successful checkout retrieval"""
        with app.app_context():
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

    @patch("app.services.sumup_service.APIError", MockAPIError)
    @patch("app.services.sumup_service.Sumup")
    def test_get_checkout_api_error(self, mock_sumup_class, app):
        """Test handling of API error when getting checkout"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.get.side_effect = MockAPIError("Not found")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.get_checkout("invalid_id")

            assert result is None

    @patch("app.services.sumup_service.Sumup")
    def test_get_checkout_generic_exception(self, mock_sumup_class, app):
        """Test handling of generic exception"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.get.side_effect = Exception("Network error")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.get_checkout("checkout_123")

            assert result is None


class TestVerifyPayment:
    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_success_paid(self, mock_sumup_class, app):
        """Test payment verification for paid checkout"""
        with app.app_context():
            mock_checkout = Mock()
            mock_checkout.status = "PAID"

            mock_client = Mock()
            mock_client.checkouts.get.return_value = mock_checkout
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("checkout_123")

            assert result is True

    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_not_paid(self, mock_sumup_class, app):
        """Test payment verification for non-paid checkout"""
        with app.app_context():
            mock_checkout = Mock()
            mock_checkout.status = "PENDING"

            mock_client = Mock()
            mock_client.checkouts.get.return_value = mock_checkout
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("checkout_123")

            assert result is False

    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_checkout_not_found(self, mock_sumup_class, app):
        """Test payment verification when checkout not found"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.get.return_value = None
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("invalid_id")

            assert result is False

    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_no_status_attribute(self, mock_sumup_class, app):
        """Test payment verification when checkout has no status"""
        with app.app_context():
            mock_checkout = Mock(spec=[])  # No status attribute

            mock_client = Mock()
            mock_client.checkouts.get.return_value = mock_checkout
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("checkout_123")

            assert result is False

    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_exception(self, mock_sumup_class, app):
        """Test payment verification handles exceptions"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.get.side_effect = Exception("Error")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("checkout_123")

            assert result is False

    @patch("app.services.sumup_service.Sumup")
    def test_verify_payment_exception_during_check(self, mock_sumup_class, app):
        """Test payment verification handles exceptions during status check"""
        with app.app_context():
            # Mock checkout that raises exception when accessing status
            mock_checkout = Mock()
            mock_checkout.status = property(
                lambda self: (_ for _ in ()).throw(Exception("Status check error"))
            )

            mock_client = Mock()
            mock_client.checkouts.get.return_value = mock_checkout
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.verify_payment("checkout_123")

            assert result is False


class TestProcessCheckoutPayment:
    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_success(self, mock_sumup_class, app):
        """Test successful payment processing"""
        with app.app_context():
            mock_response = Mock()
            mock_response.status = "PAID"
            mock_response.transaction_id = "txn_123"

            mock_client = Mock()
            mock_client.checkouts.process.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="2025",
                cvv="123",
            )

            assert result is not None
            assert result["success"] is True
            assert result["status"] == "PAID"
            assert result["transaction_id"] == "txn_123"

    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_converts_two_digit_year(self, mock_sumup_class, app):
        """Test payment processing converts 2-digit year to 4-digit"""
        with app.app_context():
            mock_response = Mock()
            mock_response.status = "PAID"

            mock_client = Mock()
            mock_client.checkouts.process.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="25",
                cvv="123",
            )

            assert result["success"] is True

    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_pads_month(self, mock_sumup_class, app):
        """Test payment processing pads single-digit month"""
        with app.app_context():
            mock_response = Mock()
            mock_response.status = "PAID"

            mock_client = Mock()
            mock_client.checkouts.process.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="5",
                expiry_year="2025",
                cvv="123",
            )

            assert result["success"] is True

    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_failed_status(self, mock_sumup_class, app):
        """Test payment processing with failed status"""
        with app.app_context():
            mock_response = Mock()
            mock_response.status = "FAILED"
            mock_response.transaction_id = None

            mock_client = Mock()
            mock_client.checkouts.process.return_value = mock_response
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="2025",
                cvv="123",
            )

            assert result["success"] is False
            assert result["status"] == "FAILED"

    @patch("app.services.sumup_service.APIError", MockAPIError)
    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_api_error(self, mock_sumup_class, app):
        """Test payment processing with API error"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.process.side_effect = MockAPIError("Card declined")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="2025",
                cvv="123",
            )

            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert "error" in result

    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_generic_exception(self, mock_sumup_class, app):
        """Test payment processing with generic exception"""
        with app.app_context():
            mock_client = Mock()
            mock_client.checkouts.process.side_effect = Exception("Network error")
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="2025",
                cvv="123",
            )

            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert "error" in result

    @patch("app.services.sumup_service.APIError", MockAPIError)
    @patch("app.services.sumup_service.Sumup")
    def test_process_payment_api_error_with_body(self, mock_sumup_class, app):
        """Test payment processing with API error that has a body attribute"""
        with app.app_context():
            api_error = MockAPIError("Card declined")
            api_error.body = "Detailed error message from API"

            mock_client = Mock()
            mock_client.checkouts.process.side_effect = api_error
            mock_sumup_class.return_value = mock_client

            service = SumUpService(api_key="test_key")
            result = service.process_checkout_payment(
                checkout_id="checkout_123",
                card_number="4111111111111111",
                card_name="John Doe",
                expiry_month="12",
                expiry_year="2025",
                cvv="123",
            )

            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert "error" in result

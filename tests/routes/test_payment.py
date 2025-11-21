"""Tests for payment routes"""

from datetime import date, timedelta
from unittest.mock import Mock, patch

import pytest

from app import db
from app.models import Credit, Membership, Payment, User


class TestShowCheckout:
    def test_show_checkout_displays_form(self, client, app):
        """Test checkout page displays payment form"""
        with client.session_transaction() as sess:
            sess["checkout_amount"] = 100.00
            sess["checkout_description"] = "Test Payment"

        response = client.get("/payment/checkout/test_checkout_123")
        assert response.status_code == 200
        assert b"test_checkout_123" in response.data

    def test_show_checkout_with_default_values(self, client):
        """Test checkout page with default values when no session"""
        response = client.get("/payment/checkout/test_checkout_123")
        assert response.status_code == 200


class TestProcessCheckout:
    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_missing_card_details(self, mock_service, client):
        """Test processing with missing card details"""
        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111"
                # Missing other required fields
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Please fill in all card details" in response.data

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_signup_payment_success(
        self, mock_email, mock_service_class, client, app, test_user
    ):
        """Test successful signup payment processing"""
        with app.app_context():
            # Create pending payment
            payment = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

            payment_id = payment.id

        # Mock successful payment
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_123",
        }
        mock_service_class.return_value = mock_service

        with client.session_transaction() as sess:
            sess["signup_user_id"] = test_user.id
            sess["signup_payment_id"] = payment_id
            sess["checkout_amount"] = 100.00
            sess["checkout_description"] = "Membership"

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment successful" in response.data

        with app.app_context():
            payment = db.session.get(Payment, payment_id)
            assert payment.status == "completed"

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_signup_payment_email_failure(
        self, mock_email, mock_service_class, client, app, test_user
    ):
        """Test successful payment but email sending fails"""
        with app.app_context():
            payment = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        # Mock successful payment but email fails
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_123",
        }
        mock_service_class.return_value = mock_service
        mock_email.side_effect = Exception("Email service down")

        with client.session_transaction() as sess:
            sess["signup_user_id"] = test_user.id
            sess["signup_payment_id"] = payment_id

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Payment should still succeed even if email fails
        with app.app_context():
            payment = db.session.get(Payment, payment_id)
            assert payment.status == "completed"

    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_signup_payment_failed(
        self, mock_service_class, client, app, test_user
    ):
        """Test failed signup payment processing"""
        with app.app_context():
            payment = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        # Mock failed payment
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": False,
            "status": "FAILED",
            "error": "Card declined",
        }
        mock_service_class.return_value = mock_service

        with client.session_transaction() as sess:
            sess["signup_user_id"] = test_user.id
            sess["signup_payment_id"] = payment_id

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment declined" in response.data

    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_pending_status(self, mock_service_class, client):
        """Test payment with pending status"""
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": False,
            "status": "PENDING",
        }
        mock_service_class.return_value = mock_service

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"pending" in response.data.lower()

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_membership_renewal(
        self, mock_email, mock_service_class, client, app, test_user
    ):
        """Test membership renewal payment"""
        with app.app_context():
            payment = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_456",
        }
        mock_service_class.return_value = mock_service

        with client.session_transaction() as sess:
            sess["membership_renewal_user_id"] = test_user.id
            sess["membership_renewal_payment_id"] = payment_id

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_membership_renewal_no_existing_membership(
        self, mock_email, mock_service_class, client, app
    ):
        """Test membership renewal creates new membership if none exists"""
        with app.app_context():
            # Create user without membership
            user = User(
                name="No Membership User",
                email="nomembership@example.com",
                phone="1234567890",
                date_of_birth=date(2000, 1, 1),
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.flush()

            payment = Payment(
                user_id=user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

            user_id = user.id
            payment_id = payment.id

        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_456",
        }
        mock_service_class.return_value = mock_service

        with client.session_transaction() as sess:
            sess["membership_renewal_user_id"] = user_id
            sess["membership_renewal_payment_id"] = payment_id

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify membership was created
        with app.app_context():
            user = db.session.get(User, user_id)
            assert user.membership is not None
            assert user.membership.status == "active"

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_membership_renewal_email_failure(
        self, mock_email, mock_service_class, client, app, test_user
    ):
        """Test membership renewal handles email failure gracefully"""
        with app.app_context():
            payment = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_456",
        }
        mock_service_class.return_value = mock_service
        mock_email.side_effect = Exception("Email service down")

        with client.session_transaction() as sess:
            sess["membership_renewal_user_id"] = test_user.id
            sess["membership_renewal_payment_id"] = payment_id

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Payment should still complete
        with app.app_context():
            payment = db.session.get(Payment, payment_id)
            assert payment.status == "completed"

    @patch("app.routes.payment.SumUpService")
    @patch("app.routes.payment.send_payment_receipt")
    def test_process_checkout_credit_purchase(
        self, mock_email, mock_service_class, client, app, test_user
    ):
        """Test credit purchase payment"""
        with app.app_context():
            payment = Payment(
                user_id=test_user.id,
                amount=50.00,
                currency="EUR",
                payment_type="credits",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_789",
        }
        mock_service_class.return_value = mock_service

        with client.session_transaction() as sess:
            sess["credit_purchase_user_id"] = test_user.id
            sess["credit_purchase_payment_id"] = payment_id
            sess["credit_purchase_quantity"] = 5

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Successfully purchased" in response.data

        with app.app_context():
            credit = Credit.query.filter_by(payment_id=payment_id).first()
            assert credit is not None
            assert credit.amount == 5

    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_exception_handling(self, mock_service_class, client):
        """Test exception handling during checkout processing"""
        mock_service = Mock()
        mock_service.process_checkout_payment.side_effect = Exception(
            "Unexpected error"
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"error" in response.data.lower()

    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_unknown_status(self, mock_service_class, client):
        """Test payment with unknown status"""
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": False,
            "status": "UNKNOWN",
            "error": "Something went wrong",
        }
        mock_service_class.return_value = mock_service

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment failed" in response.data

    @patch("app.routes.payment.SumUpService")
    def test_process_checkout_generic_success_no_session_data(
        self, mock_service_class, client
    ):
        """Test successful payment without specific session data (generic case)"""
        mock_service = Mock()
        mock_service.process_checkout_payment.return_value = {
            "success": True,
            "status": "PAID",
            "transaction_id": "txn_999",
        }
        mock_service_class.return_value = mock_service

        response = client.post(
            "/payment/checkout/test_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "John Doe",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment processed successfully" in response.data


class TestMembershipPayment:
    def test_membership_payment_requires_login(self, client):
        """Test membership payment requires authentication"""
        response = client.get("/payment/membership", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_membership_payment_page_get(self, client, test_user):
        """Test GET request to membership payment page"""
        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            response = client.get("/payment/membership")
            assert response.status_code == 200

    @patch("app.routes.payment.SumUpService")
    def test_membership_payment_post_success(
        self, mock_service_class, client, app, test_user
    ):
        """Test successful membership payment creation"""
        mock_service = Mock()
        mock_checkout = {"id": "checkout_abc", "status": "PENDING"}
        mock_service.create_checkout.return_value = mock_checkout
        mock_service_class.return_value = mock_service

        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            app.config["ANNUAL_MEMBERSHIP_COST"] = 100.00
            response = client.post("/payment/membership", follow_redirects=True)

            assert response.status_code == 200

    @patch("app.routes.payment.SumUpService")
    def test_membership_payment_checkout_failure(
        self, mock_service_class, client, app, test_user
    ):
        """Test membership payment when checkout creation fails"""
        mock_service = Mock()
        mock_service.create_checkout.return_value = None
        mock_service_class.return_value = mock_service

        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            app.config["ANNUAL_MEMBERSHIP_COST"] = 100.00

            with app.app_context():
                initial_payment_count = Payment.query.count()

            response = client.post("/payment/membership", follow_redirects=True)

            assert response.status_code == 200
            assert b"Error creating payment" in response.data

            with app.app_context():
                # Payment should be deleted after failure
                final_payment_count = Payment.query.count()
                assert final_payment_count == initial_payment_count


class TestCreditsPurchase:
    def test_credits_page_requires_login(self, client):
        response = client.get("/payment/credits", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_credits_page_logged_in(self, client, test_user):
        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            response = client.get("/payment/credits")
            assert response.status_code == 200

    @patch("app.routes.payment.SumUpService")
    def test_credits_purchase_post_success(
        self, mock_service_class, client, app, test_user
    ):
        """Test successful credit purchase"""
        mock_service = Mock()
        mock_checkout = {"id": "checkout_credits", "status": "PENDING"}
        mock_service.create_checkout.return_value = mock_checkout
        mock_service_class.return_value = mock_service

        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            app.config["ADDITIONAL_NIGHT_COST"] = 10.00
            response = client.post(
                "/payment/credits", data={"quantity": "3"}, follow_redirects=True
            )

            assert response.status_code == 200

    @patch("app.routes.payment.SumUpService")
    def test_credits_purchase_checkout_failure(
        self, mock_service_class, client, app, test_user
    ):
        """Test credit purchase when checkout creation fails"""
        mock_service = Mock()
        mock_service.create_checkout.return_value = None
        mock_service_class.return_value = mock_service

        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            app.config["ADDITIONAL_NIGHT_COST"] = 10.00
            response = client.post(
                "/payment/credits", data={"quantity": "5"}, follow_redirects=True
            )

            assert response.status_code == 200
            assert b"Error creating payment" in response.data


class TestPaymentHistory:
    def test_payment_history_requires_login(self, client):
        """Test payment history requires authentication"""
        response = client.get("/payment/history", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_payment_history_displays_user_payments(self, client, app, test_user):
        """Test payment history displays user's payments"""
        with app.app_context():
            # Create some test payments
            payment1 = Payment(
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                status="completed",
            )
            payment2 = Payment(
                user_id=test_user.id,
                amount=50.00,
                currency="EUR",
                payment_type="credits",
                status="completed",
            )
            db.session.add_all([payment1, payment2])
            db.session.commit()

        with client:
            client.post(
                "/auth/login",
                data={"email": test_user.email, "password": "password123"},
            )

            response = client.get("/payment/history")
            assert response.status_code == 200

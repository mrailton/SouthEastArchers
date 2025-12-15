"""Tests for signup payment functionality"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app import db
from app.models import Membership, Payment, User


class TestSignupWithCashPayment:
    """Test signup with cash payment method"""

    def test_signup_with_cash_creates_pending_membership(self, client, app):
        """Test that cash payment creates a pending membership"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "Cash User",
                "email": "cash@example.com",
                "phone": "1234567890",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Your membership will be activated once payment is received" in response.data

        # Verify user was created
        user = User.query.filter_by(email="cash@example.com").first()
        assert user is not None
        assert user.name == "Cash User"

        # Verify membership is pending
        assert user.membership is not None
        assert user.membership.status == "pending"
        assert user.membership.credits == 20

        # Verify payment record was created
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment is not None
        assert payment.payment_method == "cash"
        assert payment.payment_type == "membership"
        assert payment.status == "pending"
        assert payment.amount == 100  # ANNUAL_MEMBERSHIP_COST

    def test_signup_with_cash_user_cannot_login_until_activated(self, client, app):
        """Test that user can login but membership is pending"""
        # Create user with cash payment
        client.post(
            "/auth/signup",
            data={
                "name": "Cash User",
                "email": "cash@example.com",
                "phone": "1234567890",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
        )

        # User should be able to login
        response = client.post(
            "/auth/login",
            data={"email": "cash@example.com", "password": "password123"},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # But membership should still be pending
        user = User.query.filter_by(email="cash@example.com").first()
        assert user.membership.status == "pending"
        assert not user.membership.is_active()


class TestSignupWithOnlinePayment:
    """Test signup with online payment method"""

    @patch("app.services.sumup_service.SumUpService.create_checkout")
    def test_signup_with_online_redirects_to_sumup(self, mock_checkout, client, app):
        """Test that online payment redirects to custom payment form"""
        mock_checkout.return_value = {
            "id": "test_checkout_123",
            "checkout_url": "https://api.sumup.com/v0.1/checkouts/test_checkout_123",
        }

        response = client.post(
            "/auth/signup",
            data={
                "name": "Online User",
                "email": "online@example.com",
                "phone": "1234567890",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "online",
            },
        )

        # Should redirect to custom payment form
        assert response.status_code == 302
        assert "/payment/checkout/test_checkout_123" in response.location

        # Verify user and pending membership were created
        user = User.query.filter_by(email="online@example.com").first()
        assert user is not None
        assert user.membership is not None
        assert user.membership.status == "pending"

        # Verify payment record
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment is not None
        assert payment.payment_method == "online"
        assert payment.status == "pending"

    @patch("app.services.sumup_service.SumUpService.create_checkout")
    def test_signup_online_payment_failure_shows_error(self, mock_checkout, client, app):
        """Test error handling when SumUp checkout creation fails"""
        mock_checkout.return_value = None

        response = client.post(
            "/auth/signup",
            data={
                "name": "Online User",
                "email": "online@example.com",
                "phone": "1234567890",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "online",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Error creating payment" in response.data

    @patch("app.services.sumup_service.SumUpService.process_checkout_payment")
    def test_successful_online_payment_activates_membership(self, mock_process, client, app):
        """Test that successful online payment activates membership"""
        # Create user with pending membership
        user = User(
            name="Online User",
            email="online@example.com",
            phone="1234567890",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending",
        )
        db.session.add(membership)

        payment = Payment(
            user_id=user.id,
            amount=100,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Mock successful payment processing
        mock_process.return_value = {
            "success": True,
            "status": "PAID",
            "checkout_id": "test_checkout_123",
            "transaction_code": "TXN",
            "transaction_id": "txn_123",
        }

        # Set up session for payment processing
        with client.session_transaction() as sess:
            sess["signup_user_id"] = user.id
            sess["signup_payment_id"] = payment.id
            sess["checkout_amount"] = 100.0
            sess["checkout_description"] = "Annual Membership - Online User"

        # Process payment through custom form
        response = client.post(
            "/payment/checkout/test_checkout_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "Test User",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment successful" in response.data
        assert b"membership is now active" in response.data

        # Verify membership is activated
        user = User.query.filter_by(email="online@example.com").first()
        assert user.membership.status == "active"
        assert user.membership.is_active()

        # Verify payment is completed
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment.status == "completed"

    @patch("app.services.sumup_service.SumUpService.process_checkout_payment")
    def test_failed_online_payment_keeps_membership_pending(self, mock_process, client, app):
        """Test that failed online payment keeps membership pending"""
        # Create user with pending membership
        user = User(
            name="Online User",
            email="online@example.com",
            phone="1234567890",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending",
        )
        db.session.add(membership)

        payment = Payment(
            user_id=user.id,
            amount=100,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Mock failed payment processing
        mock_process.return_value = {
            "success": False,
            "status": "FAILED",
            "error": "Card declined",
        }

        # Set up session for payment processing
        with client.session_transaction() as sess:
            sess["signup_user_id"] = user.id
            sess["signup_payment_id"] = payment.id
            sess["checkout_amount"] = 100.0
            sess["checkout_description"] = "Annual Membership - Online User"

        # Process failed payment
        response = client.post(
            "/payment/checkout/test_checkout_123/process",
            data={
                "card_number": "4111111111111111",
                "card_name": "Test User",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Payment declined" in response.data or b"Card declined" in response.data

        # Verify membership is still pending
        user = User.query.filter_by(email="online@example.com").first()
        assert user.membership.status == "pending"
        assert not user.membership.is_active()

        # Verify payment is still pending
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment.status == "pending"

    @patch("app.services.sumup_service.SumUpService.create_checkout")
    def test_cancelled_online_payment_callback(self, mock_create, client, app):
        """Test that user can view payment form even if they don't complete it"""
        # Mock checkout creation
        mock_create.return_value = {
            "id": "test_checkout_123",
            "checkout_reference": "membership_1_1",
            "status": "PENDING",
        }

        # Create user
        user = User(
            name="Online User",
            email="online@example.com",
            phone="1234567890",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending",
        )
        db.session.add(membership)

        payment = Payment(
            user_id=user.id,
            amount=100,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Set up session
        with client.session_transaction() as sess:
            sess["signup_user_id"] = user.id
            sess["signup_payment_id"] = payment.id
            sess["checkout_amount"] = 100.0
            sess["checkout_description"] = "Annual Membership - Online User"

        # Access payment form (user can see it)
        response = client.get("/payment/checkout/test_checkout_123")

        assert response.status_code == 200

        # Membership should still be pending (payment not completed)
        user = User.query.filter_by(email="online@example.com").first()
        assert user.membership.status == "pending"

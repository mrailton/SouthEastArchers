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
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert (
            b"Your membership will be activated once payment is received"
            in response.data
        )

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
                "date_of_birth": "2000-01-01",
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

    def test_cash_payment_record_has_no_sumup_id(self, client, app):
        """Test that cash payment doesn't have SumUp transaction ID"""
        client.post(
            "/auth/signup",
            data={
                "name": "Cash User",
                "email": "cash@example.com",
                "phone": "1234567890",
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
        )

        user = User.query.filter_by(email="cash@example.com").first()
        payment = Payment.query.filter_by(user_id=user.id).first()

        assert payment.sumup_transaction_id is None
        assert payment.sumup_receipt_url is None


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
                "date_of_birth": "2000-01-01",
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
    def test_signup_online_payment_failure_shows_error(
        self, mock_checkout, client, app
    ):
        """Test error handling when SumUp checkout creation fails"""
        mock_checkout.return_value = None

        response = client.post(
            "/auth/signup",
            data={
                "name": "Online User",
                "email": "online@example.com",
                "phone": "1234567890",
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "online",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Error creating payment" in response.data

    @patch("app.services.sumup_service.SumUpService.process_checkout_payment")
    def test_successful_online_payment_activates_membership(
        self, mock_process, client, app
    ):
        """Test that successful online payment activates membership"""
        # Create user with pending membership
        user = User(
            name="Online User",
            email="online@example.com",
            phone="1234567890",
            date_of_birth=date(2000, 1, 1),
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
    def test_failed_online_payment_keeps_membership_pending(
        self, mock_process, client, app
    ):
        """Test that failed online payment keeps membership pending"""
        # Create user with pending membership
        user = User(
            name="Online User",
            email="online@example.com",
            phone="1234567890",
            date_of_birth=date(2000, 1, 1),
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
            date_of_birth=date(2000, 1, 1),
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


class TestAdminMembershipActivation:
    """Test admin activation of cash payment memberships"""

    def test_admin_can_activate_pending_membership(self, client, app, test_admin):
        """Test that admin can activate a pending membership"""
        # Create user with pending cash payment
        user = User(
            name="Cash User",
            email="cash@example.com",
            phone="1234567890",
            date_of_birth=date(2000, 1, 1),
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
            payment_method="cash",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Login as admin
        client.post(
            "/auth/login", data={"email": test_admin.email, "password": "admin123"}
        )

        # Activate membership
        response = client.post(
            f"/admin/members/{user.id}/membership/activate", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Membership activated" in response.data

        # Verify membership is activated
        user = User.query.filter_by(email="cash@example.com").first()
        assert user.membership.status == "active"
        assert user.membership.is_active()

        # Verify payment is completed
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment.status == "completed"

    def test_admin_cannot_activate_already_active_membership(
        self, client, app, test_admin
    ):
        """Test that admin gets info message when activating already active membership"""
        # Create user with active membership
        user = User(
            name="Active User",
            email="active@example.com",
            phone="1234567890",
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        # Login as admin
        client.post(
            "/auth/login", data={"email": test_admin.email, "password": "admin123"}
        )

        # Try to activate already active membership
        response = client.post(
            f"/admin/members/{user.id}/membership/activate", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"already active" in response.data

    def test_non_admin_cannot_activate_membership(self, client, app, test_user):
        """Test that non-admin users cannot activate memberships"""
        # Create another user with pending membership
        pending_user = User(
            name="Pending User",
            email="pending@example.com",
            phone="1234567890",
            date_of_birth=date(2000, 1, 1),
        )
        pending_user.set_password("password123")
        db.session.add(pending_user)
        db.session.flush()

        membership = Membership(
            user_id=pending_user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending",
        )
        db.session.add(membership)
        db.session.commit()

        # Login as regular user
        client.post(
            "/auth/login", data={"email": test_user.email, "password": "password123"}
        )

        # Try to activate another user's membership
        response = client.post(
            f"/admin/members/{pending_user.id}/membership/activate",
            follow_redirects=True,
        )

        # Should be redirected to login or forbidden
        assert response.status_code in [200, 403]


class TestPaymentModel:
    """Test Payment model functionality"""

    def test_payment_model_has_payment_method_field(self, app):
        """Test that Payment model has payment_method field"""
        user = User(
            name="Test User", email="test@example.com", date_of_birth=date(2000, 1, 1)
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        # Test cash payment
        cash_payment = Payment(
            user_id=user.id,
            amount=100,
            payment_type="membership",
            payment_method="cash",
        )
        db.session.add(cash_payment)

        # Test online payment
        online_payment = Payment(
            user_id=user.id, amount=5, payment_type="credits", payment_method="online"
        )
        db.session.add(online_payment)
        db.session.commit()

        assert cash_payment.payment_method == "cash"
        assert online_payment.payment_method == "online"


class TestMembershipModel:
    """Test Membership model functionality"""

    def test_membership_has_activate_method(self, app):
        """Test that Membership model has activate method"""
        user = User(
            name="Test User", email="test@example.com", date_of_birth=date(2000, 1, 1)
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
        db.session.commit()

        assert membership.status == "pending"
        assert not membership.is_active()

        # Activate membership
        membership.activate()
        db.session.commit()

        assert membership.status == "active"
        assert membership.is_active()

    def test_pending_membership_is_not_active(self, app):
        """Test that pending memberships return False for is_active()"""
        user = User(
            name="Test User", email="test@example.com", date_of_birth=date(2000, 1, 1)
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
        db.session.commit()

        # Pending membership should not be active
        assert not membership.is_active()

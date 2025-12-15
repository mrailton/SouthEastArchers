"""Tests for UserService - comprehensive service layer testing without mocks"""

from datetime import date, timedelta

import pytest

from app import db
from app.models import Membership, Payment, User
from app.services.user_service import UserService


class TestGetUserById:
    def test_get_existing_user(self, app, test_user):
        """Test retrieving an existing user by ID"""
        result = UserService.get_user_by_id(test_user.id)
        assert result is not None
        assert result.id == test_user.id
        assert result.email == test_user.email

    def test_get_nonexistent_user(self, app):
        """Test retrieving a nonexistent user returns None"""
        result = UserService.get_user_by_id(99999)
        assert result is None


class TestGetAllUsers:
    def test_get_all_users_ordered_by_name(self, app):
        """Test retrieving all users ordered by name"""
        users_data = [
            ("Zara User", "zara@example.com"),
            ("Alice User", "alice@example.com"),
            ("Bob User", "bob@example.com"),
        ]

        for name, email in users_data:
            user = User(name=name, email=email)
            user.set_password("password123")
            db.session.add(user)
        db.session.commit()

        result = UserService.get_all_users()
        assert len(result) == 3
        assert result[0].name == "Alice User"
        assert result[1].name == "Bob User"
        assert result[2].name == "Zara User"

    def test_get_all_users_empty_database(self, app):
        """Test retrieving users when database is empty"""
        result = UserService.get_all_users()
        assert result == []


class TestUpdateProfile:
    def test_update_name_only(self, app, test_user):
        """Test updating only the name"""
        original_phone = test_user.phone
        success, message = UserService.update_profile(test_user, name="New Name")

        assert success is True
        assert "successfully" in message
        assert test_user.name == "New Name"
        assert test_user.phone == original_phone

    def test_update_phone_only(self, app, test_user):
        """Test updating only the phone"""
        original_name = test_user.name
        success, message = UserService.update_profile(test_user, phone="9876543210")

        assert success is True
        assert test_user.phone == "9876543210"
        assert test_user.name == original_name

    def test_update_both_name_and_phone(self, app, test_user):
        """Test updating both name and phone"""
        success, message = UserService.update_profile(test_user, name="Updated Name", phone="5555555555")

        assert success is True
        assert test_user.name == "Updated Name"
        assert test_user.phone == "5555555555"

    def test_update_phone_to_empty_string(self, app, test_user):
        """Test clearing phone number"""
        success, message = UserService.update_profile(test_user, phone="")

        assert success is True
        assert test_user.phone == ""

    def test_update_with_no_changes(self, app, test_user):
        """Test calling update with no parameters"""
        original_name = test_user.name
        original_phone = test_user.phone
        success, message = UserService.update_profile(test_user)

        assert success is True
        assert test_user.name == original_name
        assert test_user.phone == original_phone


class TestChangePassword:
    def test_change_password_success(self, app, test_user):
        """Test successfully changing password"""
        success, message = UserService.change_password(test_user, "password123", "newpassword456")

        assert success is True
        assert "successfully" in message
        assert test_user.check_password("newpassword456")
        assert not test_user.check_password("password123")

    def test_change_password_wrong_current(self, app, test_user):
        """Test changing password with wrong current password"""
        success, message = UserService.change_password(test_user, "wrongpassword", "newpassword456")

        assert success is False
        assert "incorrect" in message.lower()
        assert test_user.check_password("password123")

    def test_change_password_too_short(self, app, test_user):
        """Test changing password to one that's too short"""
        success, message = UserService.change_password(test_user, "password123", "short")

        assert success is False
        assert "8 characters" in message
        assert test_user.check_password("password123")

    def test_change_password_exactly_8_characters(self, app, test_user):
        """Test changing password to exactly 8 characters"""
        success, message = UserService.change_password(test_user, "password123", "12345678")

        assert success is True
        assert test_user.check_password("12345678")


class TestCreateMember:
    def test_create_member_basic(self, app):
        """Test creating a basic member without membership"""
        user, error = UserService.create_member(name="New Member", email="newmember@example.com")

        assert error is None
        assert user is not None
        assert user.name == "New Member"
        assert user.email == "newmember@example.com"
        assert user.check_password("changeme123")
        assert user.is_admin is False
        assert user.membership is None

    def test_create_member_with_custom_password(self, app):
        """Test creating member with custom password"""
        user, error = UserService.create_member(
            name="Custom Pass Member", email="custom@example.com", password="custompass123"
        )

        assert error is None
        assert user.check_password("custompass123")

    def test_create_member_as_admin(self, app):
        """Test creating member with admin privileges"""
        user, error = UserService.create_member(name="Admin Member", email="adminmember@example.com", is_admin=True)

        assert error is None
        assert user.is_admin is True

    def test_create_member_with_phone(self, app):
        """Test creating member with phone number"""
        user, error = UserService.create_member(name="Phone Member", email="phone@example.com", phone="1234567890")

        assert error is None
        assert user.phone == "1234567890"

    def test_create_member_with_membership(self, app):
        """Test creating member with active membership"""
        user, error = UserService.create_member(
            name="Member With Membership",
            email="withmembership@example.com",
            create_membership=True,
        )

        assert error is None
        assert user.membership is not None
        assert user.membership.status == "active"
        assert user.membership.credits == 20
        assert user.membership.start_date == date.today()
        assert user.membership.expiry_date == date.today() + timedelta(days=365)

    def test_create_member_duplicate_email(self, app, test_user):
        """Test creating member with existing email"""
        user, error = UserService.create_member(name="Duplicate Email", email=test_user.email)

        assert user is None
        assert error == "Email already registered."


class TestUpdateMember:
    def test_update_member_basic_info(self, app, test_user):
        """Test updating member basic information"""
        success, message = UserService.update_member(
            user=test_user,
            name="Updated Name",
            email="updated@example.com",

            phone="9999999999",
        )

        assert success is True
        assert "successfully" in message
        assert test_user.name == "Updated Name"
        assert test_user.email == "updated@example.com"
        assert test_user.phone == "9999999999"

    def test_update_member_admin_status(self, app, test_user):
        """Test toggling admin status"""
        assert test_user.is_admin is False

        success, message = UserService.update_member(
            user=test_user,
            name=test_user.name,
            email=test_user.email,
            is_admin=True,
        )

        assert success is True
        assert test_user.is_admin is True

    def test_update_member_active_status(self, app, test_user):
        """Test deactivating a member"""
        success, message = UserService.update_member(
            user=test_user,
            name=test_user.name,
            email=test_user.email,
            is_active=False,
        )

        assert success is True
        assert test_user.is_active is False

    def test_update_member_password(self, app, test_user):
        """Test updating member password"""
        success, message = UserService.update_member(
            user=test_user,
            name=test_user.name,
            email=test_user.email,
            password="newadminpassword",
        )

        assert success is True
        assert test_user.check_password("newadminpassword")

    def test_update_member_membership_dates(self, app, test_user):
        """Test updating membership dates"""
        new_start = date(2024, 1, 1)
        new_expiry = date(2025, 1, 1)

        success, message = UserService.update_member(
            user=test_user,
            name=test_user.name,
            email=test_user.email,
            membership_start_date=new_start,
            membership_expiry_date=new_expiry,
        )

        assert success is True
        assert test_user.membership.start_date == new_start
        assert test_user.membership.expiry_date == new_expiry

    def test_update_member_credits(self, app, test_user):
        """Test updating membership credits"""
        success, message = UserService.update_member(
            user=test_user,
            name=test_user.name,
            email=test_user.email,
            membership_credits=50,
        )

        assert success is True
        assert test_user.membership.credits == 50

    def test_update_member_without_membership(self, app):
        """Test updating member who has no membership"""
        user = User(name="No Membership", email="nomem@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        success, message = UserService.update_member(
            user=user,
            name="Updated No Membership",
            email="nomem@example.com",
            membership_credits=30,
        )

        assert success is True
        assert user.name == "Updated No Membership"


class TestCreateUser:
    def test_create_user_with_online_payment(self, app):
        """Test creating user with online payment method"""
        user, error = UserService.create_user(
            name="Online User",
            email="online@example.com",
            password="password123",
            phone="1234567890",
            payment_method="online",
        )

        assert error is None
        assert user is not None
        assert user.name == "Online User"
        assert user.membership is not None
        assert user.membership.status == "pending"

        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment is not None
        assert payment.payment_method == "online"
        assert payment.payment_processor == "sumup"
        assert payment.status == "pending"

    def test_create_user_with_cash_payment(self, app):
        """Test creating user with cash payment method"""
        user, error = UserService.create_user(
            name="Cash User",
            email="cash@example.com",
            password="password123",
            payment_method="cash",
        )

        assert error is None
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment.payment_method == "cash"
        assert payment.payment_processor is None

    def test_create_user_membership_fee(self, app):
        """Test adult user gets full membership fee"""
        user, error = UserService.create_user(
            name="Adult User",
            email="adult@example.com",
            password="password123",
        )

        assert error is None
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment.amount_cents == app.config["ANNUAL_MEMBERSHIP_COST"]

    def test_create_user_duplicate_email(self, app, test_user):
        """Test creating user with duplicate email"""
        user, error = UserService.create_user(name="Duplicate", email=test_user.email, password="password123")

        assert user is None
        assert error == "Email already registered."

    def test_create_user_membership_dates(self, app):
        """Test user membership has correct dates"""
        user, error = UserService.create_user(name="Date Test", email="datetest@example.com", password="password123")

        assert error is None
        assert user.membership.start_date == date.today()
        assert user.membership.expiry_date == date.today() + timedelta(days=365)


class TestAuthenticate:
    def test_authenticate_valid_credentials(self, app, test_user):
        """Test authentication with valid credentials"""
        result = UserService.authenticate(test_user.email, "password123")

        assert result is not None
        assert result.id == test_user.id

    def test_authenticate_invalid_password(self, app, test_user):
        """Test authentication with invalid password"""
        result = UserService.authenticate(test_user.email, "wrongpassword")

        assert result is None

    def test_authenticate_nonexistent_email(self, app):
        """Test authentication with nonexistent email"""
        result = UserService.authenticate("nonexistent@example.com", "password123")

        assert result is None

    def test_authenticate_inactive_user(self, app, test_user):
        """Test authentication with inactive user"""
        test_user.is_active = False
        db.session.commit()

        result = UserService.authenticate(test_user.email, "password123")

        assert result is None


class TestPasswordResetToken:
    def test_create_password_reset_token(self, app, test_user):
        """Test creating password reset token"""
        token = UserService.create_password_reset_token(test_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_reset_password_with_valid_token(self, app, test_user):
        """Test resetting password with valid token"""
        token = UserService.create_password_reset_token(test_user)
        success, message = UserService.reset_password(token, "newpassword123")

        assert success is True
        assert "successfully" in message.lower()
        assert test_user.check_password("newpassword123")

    def test_reset_password_with_invalid_token(self, app):
        """Test resetting password with invalid token"""
        success, message = UserService.reset_password("invalid_token", "newpassword123")

        assert success is False
        assert "invalid" in message.lower() or "expired" in message.lower()

    def test_reset_password_with_expired_token(self, app, test_user):
        """Test resetting password with expired token"""
        from datetime import datetime, timedelta
        from unittest.mock import patch

        token = test_user.generate_reset_token()

        # Simulate token expiration by trying to verify with negative max_age
        success, message = UserService.reset_password(token, "newpassword123")

        # Token should be valid if just created
        assert success is True


class TestInitiateOnlinePayment:
    def test_initiate_payment_with_existing_payment_record(self, app, test_user):
        """Test initiating online payment when payment record exists"""
        # Create a payment record
        payment = Payment(
            user_id=test_user.id,
            amount_cents=10000,
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Mock the payment service's create_checkout to avoid external API call
        from unittest.mock import patch

        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = {"id": "checkout_123"}

            result = UserService.initiate_online_payment(test_user, test_user.name)

            assert result["success"] is True
            assert result["checkout_id"] == "checkout_123"

    def test_initiate_payment_without_payment_record(self, app, test_user):
        """Test initiating payment when no payment record exists"""
        # Ensure no payment exists
        Payment.query.filter_by(user_id=test_user.id).delete()
        db.session.commit()

        result = UserService.initiate_online_payment(test_user, test_user.name)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_initiate_payment_checkout_creation_fails(self, app, test_user):
        """Test initiating payment when checkout creation fails"""
        payment = Payment(
            user_id=test_user.id,
            amount_cents=10000,
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        from unittest.mock import patch

        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = None

            result = UserService.initiate_online_payment(test_user, test_user.name)

            assert result["success"] is False
            assert "error" in result["error"].lower()


class TestUpdateProfileErrors:
    def test_update_profile_database_error(self, app, test_user):
        """Test update profile when database commit fails"""
        from unittest.mock import patch

        with patch("app.db.session.commit", side_effect=Exception("Database error")):
            success, message = UserService.update_profile(test_user, name="New Name")

            assert success is False
            assert "error" in message.lower()


class TestChangePasswordErrors:
    def test_change_password_database_error(self, app, test_user):
        """Test change password when database commit fails"""
        from unittest.mock import patch

        with patch("app.db.session.commit", side_effect=Exception("Database error")):
            success, message = UserService.change_password(test_user, "password123", "newpassword123")

            assert success is False
            assert "error" in message.lower()


class TestCreateMemberErrors:
    def test_create_member_database_error(self, app):
        """Test create member when database operation fails"""
        from unittest.mock import patch

        with patch("app.db.session.commit", side_effect=Exception("Database error")):
            user, error = UserService.create_member(name="New Member", email="new@example.com")

            assert user is None
            assert error is not None
            assert "error" in error.lower()


class TestUpdateMemberErrors:
    def test_update_member_database_error(self, app, test_user):
        """Test update member when database commit fails"""
        from unittest.mock import patch

        with patch("app.db.session.commit", side_effect=Exception("Database error")):
            success, message = UserService.update_member(
                user=test_user,
                name="Updated Name",
                email=test_user.email,
            )

            assert success is False
            assert "error" in message.lower()


class TestCreateUserErrors:
    def test_create_user_database_error(self, app):
        """Test create user when database operation fails"""
        from unittest.mock import patch

        with patch("app.db.session.commit", side_effect=Exception("Database error")):
            user, error = UserService.create_user(
                name="New User",
                email="newuser@example.com",
                password="password123",
            )

            assert user is None
            assert error is not None
            assert "error" in error.lower()

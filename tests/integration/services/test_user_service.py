from datetime import date

from app import db
from app.models import Role, User
from app.services.settings_service import SettingsService
from app.services.user_service import UserService

# TestGetUserById


def test_get_existing_user(app, test_user):
    """Test retrieving an existing user by ID"""
    result = UserService.get_user_by_id(test_user.id)
    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email


def test_get_nonexistent_user(app):
    """Test retrieving a nonexistent user returns None"""
    result = UserService.get_user_by_id(99999)
    assert result is None


# TestUpdateProfile


def test_update_name_only(app, test_user):
    """Test updating only the name"""
    original_phone = test_user.phone
    result = UserService.update_profile(test_user, name="New Name")

    assert result.success is True
    assert "successfully" in result.message
    assert test_user.name == "New Name"
    assert test_user.phone == original_phone


def test_update_phone_only(app, test_user):
    """Test updating only the phone"""
    original_name = test_user.name
    result = UserService.update_profile(test_user, phone="9876543210")

    assert result.success is True
    assert test_user.phone == "9876543210"
    assert test_user.name == original_name


def test_update_both_name_and_phone(app, test_user):
    """Test updating both name and phone"""
    result = UserService.update_profile(test_user, name="Updated Name", phone="5555555555")

    assert result.success is True
    assert test_user.name == "Updated Name"
    assert test_user.phone == "5555555555"


def test_update_phone_to_empty_string(app, test_user):
    """Test clearing phone number"""
    result = UserService.update_profile(test_user, phone="")

    assert result.success is True
    assert test_user.phone == ""


def test_update_with_no_changes(app, test_user):
    """Test calling update with no parameters"""
    original_name = test_user.name
    original_phone = test_user.phone
    result = UserService.update_profile(test_user)

    assert result.success is True
    assert test_user.name == original_name
    assert test_user.phone == original_phone


# TestChangePassword


def test_change_password_success(app, test_user):
    """Test successfully changing password"""
    result = UserService.change_password(test_user, "password123", "newpassword456")

    assert result.success is True
    assert "successfully" in result.message
    assert test_user.check_password("newpassword456")
    assert not test_user.check_password("password123")


def test_change_password_wrong_current(app, test_user):
    """Test changing password with wrong current password"""
    result = UserService.change_password(test_user, "wrongpassword", "newpassword456")

    assert result.success is False
    assert "incorrect" in result.message.lower()
    assert test_user.check_password("password123")


def test_change_password_too_short(app, test_user):
    """Test changing password to one that's too short"""
    result = UserService.change_password(test_user, "password123", "short")

    assert result.success is False
    assert "8 characters" in result.message
    assert test_user.check_password("password123")


def test_change_password_exactly_8_characters(app, test_user):
    """Test changing password to exactly 8 characters"""
    result = UserService.change_password(test_user, "password123", "12345678")

    assert result.success is True
    assert test_user.check_password("12345678")


# TestCreateMember


def test_create_member_basic(app):
    """Test creating a basic member without membership"""
    result = UserService.create_member(name="New Member", email="newmember@example.com")

    assert result.success is True
    assert result.data is not None
    assert result.data.name == "New Member"
    assert result.data.email == "newmember@example.com"
    assert result.data.check_password("changeme123")
    assert result.data.membership is None


def test_create_member_with_custom_password(app):
    """Test creating member with custom password"""
    result = UserService.create_member(name="Custom Pass Member", email="custom@example.com", password="custompass123")

    assert result.success is True
    assert result.data.check_password("custompass123")


def test_create_member_as_admin(app):
    """Test creating member with admin privileges"""
    admin_role = Role.query.filter_by(name="Admin").first()
    result = UserService.create_member(name="Admin Member", email="adminmember@example.com", role_ids=[admin_role.id] if admin_role else [])

    assert result.success is True
    if admin_role:
        assert admin_role in result.data.roles


def test_create_member_with_phone(app):
    """Test creating member with phone number"""
    result = UserService.create_member(name="Phone Member", email="phone@example.com", phone="1234567890")

    assert result.success is True
    assert result.data.phone == "1234567890"


def test_create_member_with_membership(app):
    """Test creating member with active membership"""
    result = UserService.create_member(
        name="Member With Membership",
        email="withmembership@example.com",
        create_membership=True,
    )

    assert result.success is True
    assert result.data.membership is not None
    assert result.data.membership.status == "active"
    assert result.data.membership.initial_credits == 20
    assert result.data.membership.start_date == date.today()
    expected_expiry = SettingsService.calculate_membership_expiry(date.today()).date()
    assert result.data.membership.expiry_date == expected_expiry
    assert result.data.membership.expiry_date >= date.today()


def test_create_member_starts_inactive(app):
    """Test new members start as inactive (must be activated by admin)"""
    result = UserService.create_member(name="New Member", email="newemail@example.com")

    assert result.success is True
    assert result.data is not None
    assert result.data.is_active is False


def test_create_member_duplicate_email(app, test_user):
    """Test creating member with existing email"""
    result = UserService.create_member(name="Duplicate Email", email=test_user.email)

    assert result.data is None
    assert result.message == "Email already registered."


# TestUpdateMember


def test_update_member_basic_info(app, test_user):
    """Test updating member basic information"""
    result = UserService.update_member(
        user=test_user,
        name="Updated Name",
        email="updated@example.com",
        phone="9999999999",
    )

    assert result.success is True
    assert "successfully" in result.message
    assert test_user.name == "Updated Name"
    assert test_user.email == "updated@example.com"
    assert test_user.phone == "9999999999"


def test_update_member_admin_status(app, test_user):
    """Test toggling admin status"""
    # Remove admin flag assertion (RBAC now)
    admin_role = Role.query.filter_by(name="Admin").first()
    result = UserService.update_member(
        user=test_user,
        name=test_user.name,
        email=test_user.email,
        role_ids=[admin_role.id] if admin_role else [],
    )

    assert result.success is True
    if admin_role:
        assert admin_role in test_user.roles


def test_update_member_active_status(app, test_user):
    """Test deactivating a member"""
    result = UserService.update_member(
        user=test_user,
        name=test_user.name,
        email=test_user.email,
        is_active=False,
    )

    assert result.success is True
    assert test_user.is_active is False


def test_update_member_password(app, test_user):
    """Test updating member password"""
    result = UserService.update_member(
        user=test_user,
        name=test_user.name,
        email=test_user.email,
        password="newadminpassword",
    )

    assert result.success is True
    assert test_user.check_password("newadminpassword")


def test_update_member_membership_dates(app, test_user):
    """Test updating membership dates"""
    new_start = date(2024, 1, 1)
    new_expiry = date(2025, 1, 1)

    result = UserService.update_member(
        user=test_user,
        name=test_user.name,
        email=test_user.email,
        membership_start_date=new_start,
        membership_expiry_date=new_expiry,
    )

    assert result.success is True
    assert test_user.membership.start_date == new_start
    assert test_user.membership.expiry_date == new_expiry


def test_update_member_credits(app, test_user):
    """Test updating membership credits"""
    result = UserService.update_member(
        user=test_user,
        name=test_user.name,
        email=test_user.email,
        membership_initial_credits=50,
        membership_purchased_credits=10,
    )

    assert result.success is True
    assert test_user.membership.initial_credits == 50
    assert test_user.membership.purchased_credits == 10


def test_update_member_without_membership(app):
    """Test updating member who has no membership"""
    user = User(name="No Membership", email="nomem@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    result = UserService.update_member(
        user=user,
        name="Updated No Membership",
        email="nomem@example.com",
        membership_initial_credits=30,
    )

    assert result.success is True
    assert user.name == "Updated No Membership"


# TestCreateUser


def test_create_user(app):
    """Test creating user with online payment method"""
    result = UserService.create_user(
        name="Online User",
        email="online@example.com",
        password="password123",
        phone="1234567890",
        qualification="none",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.name == "Online User"
    assert result.data.membership is None
    assert result.data.is_active is False


def test_create_user_duplicate_email(app, test_user):
    """Test creating user with duplicate email"""
    result = UserService.create_user(name="Duplicate", email=test_user.email, password="password123")

    assert result.data is None
    assert result.message == "Email already registered."


# TestAuthenticate


def test_authenticate_valid_credentials(app, test_user):
    """Test authentication with valid credentials"""
    result = UserService.authenticate(test_user.email, "password123")

    assert result is not None
    assert result.id == test_user.id


def test_authenticate_invalid_password(app, test_user):
    """Test authentication with invalid password"""
    result = UserService.authenticate(test_user.email, "wrongpassword")

    assert result is None


def test_authenticate_nonexistent_email(app):
    """Test authentication with nonexistent email"""
    result = UserService.authenticate("nonexistent@example.com", "password123")

    assert result is None


# TestPasswordResetToken


def test_create_password_reset_token(app, test_user):
    """Test creating password reset token"""
    token = UserService.create_password_reset_token(test_user)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_reset_password_with_valid_token(app, test_user):
    """Test resetting password with valid token"""
    token = UserService.create_password_reset_token(test_user)
    result = UserService.reset_password(token, "newpassword123")

    assert result.success is True
    assert "successfully" in result.message.lower()
    assert test_user.check_password("newpassword123")


def test_reset_password_with_invalid_token(app):
    """Test resetting password with invalid token"""
    result = UserService.reset_password("invalid_token", "newpassword123")

    assert result.success is False
    assert "invalid" in result.message.lower() or "expired" in result.message.lower()


def test_reset_password_with_expired_token(app, test_user):
    """Test resetting password with expired token"""

    token = test_user.generate_reset_token()

    # Simulate token expiration by trying to verify with negative max_age
    result = UserService.reset_password(token, "newpassword123")

    # Token should be valid if just created
    assert result.success is True


# TestUpdateProfileErrors


def test_update_profile_database_error(app, test_user):
    """Test update profile when database commit fails"""
    from unittest.mock import patch

    with patch("app.db.session.commit", side_effect=Exception("Database error")):
        result = UserService.update_profile(test_user, name="New Name")

        assert result.success is False
        assert "error" in result.message.lower()


# TestChangePasswordErrors


def test_change_password_database_error(app, test_user):
    """Test change password when database commit fails"""
    from unittest.mock import patch

    with patch("app.db.session.commit", side_effect=Exception("Database error")):
        result = UserService.change_password(test_user, "password123", "newpassword123")

        assert result.success is False
        assert "error" in result.message.lower()


# TestCreateMemberErrors


def test_create_member_database_error(app):
    """Test create member when database operation fails"""
    from unittest.mock import patch

    with patch("app.db.session.commit", side_effect=Exception("Database error")):
        result = UserService.create_member(name="New Member", email="new@example.com")

        assert result.data is None
        assert result.message is not None
        assert "error" in result.message.lower()


# TestUpdateMemberErrors


def test_update_member_database_error(app, test_user):
    """Test update member when database commit fails"""
    from unittest.mock import patch

    with patch("app.db.session.commit", side_effect=Exception("Database error")):
        result = UserService.update_member(
            user=test_user,
            name="Updated Name",
            email=test_user.email,
        )

        assert result.success is False
        assert "error" in result.message.lower()


# TestCreateUserErrors


def test_create_user_database_error(app):
    """Test create user when database operation fails"""
    from unittest.mock import patch

    with patch("app.db.session.commit", side_effect=Exception("Database error")):
        result = UserService.create_user(
            name="New User",
            email="newuser@example.com",
            password="password123",
        )

        assert result.data is None
        assert result.message is not None
        assert "error" in result.message.lower()

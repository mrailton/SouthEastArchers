"""
Tests for the accounts app.
"""
import pytest
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from django.test import Client
from accounts.forms import LoginForm, RegistrationForm
from accounts.backends import EmailBackend
from memberships.models import Membership

User = get_user_model()


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.models
@pytest.mark.django_db
class TestUserModel:
    """Test the custom User model."""

    def test_create_user(self):
        """Test creating a user with email."""
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            phone='1234567890',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.phone == '1234567890'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_admin is False
        assert user.check_password('testpass123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User',
            phone='0987654321',
            password='adminpass123'
        )
        assert admin.email == 'admin@example.com'
        assert admin.is_active is True
        assert admin.is_staff is True
        assert admin.is_admin is True
        assert admin.is_superuser is True

    def test_user_email_unique(self):
        """Test that email must be unique."""
        User.objects.create_user(
            email='unique@example.com',
            name='First User',
            password='pass123'
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                email='unique@example.com',
                name='Second User',
                password='pass456'
            )

    def test_user_string_representation(self):
        """Test __str__ method returns name."""
        user = User.objects.create_user(
            email='string@example.com',
            name='String User',
            password='pass123'
        )
        assert str(user) == 'String User'

    def test_user_has_perm(self):
        """Test has_perm method for superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin',
            password='pass123'
        )
        assert admin.has_perm('any.permission') is True

    def test_user_has_module_perms(self):
        """Test has_module_perms method for superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin',
            password='pass123'
        )
        assert admin.has_module_perms('accounts') is True

    def test_current_membership_property(self, user, membership):
        """Test current_membership property returns active membership."""
        current = user.current_membership
        assert current is not None
        assert current.is_active is True
        assert current == membership

    def test_current_membership_none_when_no_active(self, user, expired_membership):
        """Test current_membership returns None when no active membership."""
        assert user.current_membership is None

    def test_total_credits_property(self, user, membership):
        """Test total_credits property sums credits from active membership."""
        assert user.total_credits == 20

    def test_total_credits_zero_when_no_membership(self, user):
        """Test total_credits is 0 when no active membership."""
        assert user.total_credits == 0

    def test_create_user_without_email_raises_error(self):
        """Test creating user without email raises ValueError."""
        with pytest.raises(ValueError, match='The Email field must be set'):
            User.objects.create_user(email='', password='test123')

    def test_create_superuser_without_is_staff_raises_error(self):
        """Test creating superuser with is_staff=False raises ValueError."""
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                email='admin@test.com',
                password='test123',
                is_staff=False
            )

    def test_create_superuser_without_is_superuser_raises_error(self):
        """Test creating superuser with is_superuser=False raises ValueError."""
        with pytest.raises(ValueError, match='Superuser must have is_superuser=True'):
            User.objects.create_superuser(
                email='admin@test.com',
                password='test123',
                is_superuser=False
            )


# ============================================================================
# AUTHENTICATION BACKEND TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestEmailBackend:
    """Test the custom EmailBackend authentication."""

    def test_authenticate_with_valid_credentials(self, user, user_data):
        """Test authentication with valid email and password."""
        backend = EmailBackend()
        authenticated_user = backend.authenticate(
            request=None,
            username=user_data['email'],
            password=user_data['password']
        )
        assert authenticated_user is not None
        assert authenticated_user.email == user_data['email']

    def test_authenticate_with_invalid_password(self, user, user_data):
        """Test authentication fails with wrong password."""
        backend = EmailBackend()
        authenticated_user = backend.authenticate(
            request=None,
            username=user_data['email'],
            password='wrongpassword'
        )
        assert authenticated_user is None

    def test_authenticate_with_nonexistent_user(self):
        """Test authentication fails with nonexistent email."""
        backend = EmailBackend()
        authenticated_user = backend.authenticate(
            request=None,
            username='nonexistent@example.com',
            password='anypass'
        )
        assert authenticated_user is None

    def test_get_user(self, user):
        """Test get_user returns correct user."""
        backend = EmailBackend()
        retrieved_user = backend.get_user(user.id)
        assert retrieved_user == user

    def test_get_user_nonexistent(self):
        """Test get_user returns None for nonexistent ID."""
        backend = EmailBackend()
        retrieved_user = backend.get_user(99999)
        assert retrieved_user is None


# ============================================================================
# FORM TESTS
# ============================================================================

@pytest.mark.forms
@pytest.mark.django_db
class TestLoginForm:
    """Test the LoginForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = LoginForm(data={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        assert form.is_valid()

    def test_missing_email(self):
        """Test form validation fails without email."""
        form = LoginForm(data={
            'password': 'testpass123'
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_missing_password(self):
        """Test form validation fails without password."""
        form = LoginForm(data={
            'email': 'test@example.com'
        })
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_invalid_email_format(self):
        """Test form validation fails with invalid email format."""
        form = LoginForm(data={
            'email': 'not-an-email',
            'password': 'testpass123'
        })
        assert not form.is_valid()
        assert 'email' in form.errors


@pytest.mark.forms
@pytest.mark.django_db
class TestRegistrationForm:
    """Test the RegistrationForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = RegistrationForm(data={
            'email': 'newuser@example.com',
            'name': 'New User',
            'phone': '1234567890',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        assert form.is_valid()

    def test_passwords_must_match(self):
        """Test form validation fails when passwords don't match."""
        form = RegistrationForm(data={
            'email': 'newuser@example.com',
            'name': 'New User',
            'phone': '1234567890',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'
        })
        assert not form.is_valid()
        assert '__all__' in form.errors  # General form error for password mismatch

    def test_duplicate_email(self, user):
        """Test form validation fails with existing email."""
        form = RegistrationForm(data={
            'email': user.email,  # Already exists
            'name': 'Another User',
            'phone': '0987654321',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_missing_required_fields(self):
        """Test form validation fails with missing fields."""
        form = RegistrationForm(data={})
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'name' in form.errors
        assert 'password1' in form.errors
        assert 'password2' in form.errors


# ============================================================================
# VIEW TESTS
# ============================================================================

@pytest.mark.views
@pytest.mark.django_db
class TestLoginView:
    """Test the login view."""

    def test_login_page_loads(self, client):
        """Test login page loads successfully."""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_login_with_valid_credentials(self, client, user, user_data):
        """Test login with valid credentials."""
        response = client.post(reverse('accounts:login'), {
            'email': user_data['email'],
            'password': user_data['password']
        })
        assert response.status_code == 302  # Redirect after successful login
        assert response.url == reverse('memberships:dashboard')

    def test_login_with_invalid_credentials(self, client, user):
        """Test login fails with invalid credentials."""
        response = client.post(reverse('accounts:login'), {
            'email': user.email,
            'password': 'wrongpassword'
        })
        assert response.status_code == 200  # Stays on login page
        assert 'Invalid email or password' in str(response.content)

    def test_login_redirects_to_next_parameter(self, client, user, user_data):
        """Test login redirects to 'next' parameter if provided."""
        next_url = reverse('memberships:purchase_credits')
        response = client.post(
            reverse('accounts:login') + f'?next={next_url}',
            {
                'email': user_data['email'],
                'password': user_data['password']
            }
        )
        assert response.status_code == 302
        assert response.url == next_url

    def test_logged_in_user_redirected_from_login(self, authenticated_client):
        """Test already logged-in users are redirected from login page."""
        response = authenticated_client.get(reverse('accounts:login'))
        assert response.status_code == 302


@pytest.mark.views
@pytest.mark.django_db
class TestRegisterView:
    """Test the registration view."""

    def test_register_page_loads(self, client):
        """Test registration page loads successfully."""
        response = client.get(reverse('accounts:register'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_register_creates_user_and_membership(self, client):
        """Test registration creates user and membership."""
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'phone': '1234567890',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = client.post(reverse('accounts:register'), data)

        # Check user was created
        assert User.objects.filter(email='newuser@example.com').exists()
        user = User.objects.get(email='newuser@example.com')

        # Check membership was created
        assert Membership.objects.filter(user=user, is_active=True).exists()
        membership = Membership.objects.get(user=user)
        assert membership.credits_remaining == 20

        # Check redirect
        assert response.status_code == 302
        assert response.url == reverse('memberships:dashboard')

    def test_register_with_invalid_data(self, client):
        """Test registration fails with invalid data."""
        data = {
            'email': 'invalid-email',
            'name': 'New User',
            'phone': '1234567890',
            'password1': 'pass',
            'password2': 'different'
        }
        response = client.post(reverse('accounts:register'), data)
        assert response.status_code == 200  # Stays on registration page
        assert User.objects.filter(email='invalid-email').exists() is False

    def test_logged_in_user_redirected_from_register(self, authenticated_client):
        """Test already logged-in users are redirected from register page."""
        response = authenticated_client.get(reverse('accounts:register'))
        assert response.status_code == 302


@pytest.mark.views
@pytest.mark.django_db
class TestLogoutView:
    """Test the logout view."""

    def test_logout_redirects(self, authenticated_client):
        """Test logout redirects to home page."""
        response = authenticated_client.get(reverse('accounts:logout'))
        assert response.status_code == 302
        assert response.url == reverse('core:index')

    def test_user_logged_out(self, authenticated_client):
        """Test user is actually logged out."""
        authenticated_client.get(reverse('accounts:logout'))
        response = authenticated_client.get(reverse('memberships:dashboard'))
        # Should redirect to login because user is no longer authenticated
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

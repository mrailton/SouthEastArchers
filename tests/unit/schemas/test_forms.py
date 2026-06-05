import pytest
from pydantic import ValidationError

from app.schemas.forms import (
    ChangePasswordForm,
    ForgotPasswordForm,
    LoginForm,
    ProfileForm,
    ResetPasswordForm,
    SignupForm,
    forgot_password_form,
    login_form,
    reset_password_form,
    signup_form,
)


def test_login_form_factory():
    form = login_form(csrf_token="t", email="a@example.com", password="secret")
    assert isinstance(form, LoginForm)


def test_signup_form_factory_and_password_mismatch():
    with pytest.raises(ValidationError):
        SignupForm(
            name="Test User",
            email="test@example.com",
            password="password123",
            password_confirm="different",
        )
    form = signup_form(
        name="Test User",
        email="test@example.com",
        password="password123",
        password_confirm="password123",
    )
    assert isinstance(form, SignupForm)


def test_forgot_password_form_factory():
    form = forgot_password_form(email="a@example.com")
    assert isinstance(form, ForgotPasswordForm)


def test_reset_password_form_mismatch():
    with pytest.raises(ValidationError):
        ResetPasswordForm(password="password123", password_confirm="x")


def test_reset_password_form_factory():
    form = reset_password_form(password="password123", password_confirm="password123")
    assert isinstance(form, ResetPasswordForm)


def test_profile_form_min_length():
    with pytest.raises(ValidationError):
        ProfileForm(name="A")


def test_change_password_mismatch():
    with pytest.raises(ValidationError):
        ChangePasswordForm(
            current_password="old",
            new_password="newpassword",
            confirm_password="different",
        )

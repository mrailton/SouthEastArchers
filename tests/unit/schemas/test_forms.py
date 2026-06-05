import pytest
from pydantic import ValidationError

from app.schemas.form_helpers import parse_form
from app.schemas.forms import (
    ChangePasswordForm,
    ForgotPasswordForm,
    LoginForm,
    ProfileForm,
    ResetPasswordForm,
    SignupForm,
)
from app.utils.formdata import MultiDict


def test_login_form_parse():
    data = MultiDict()
    data.add("csrf_token", "t")
    data.add("email", "a@example.com")
    data.add("password", "secret")
    form, errors, _values = parse_form(LoginForm, data)
    assert errors == {}
    assert form is not None
    assert isinstance(form, LoginForm)


def test_signup_form_parse_and_password_mismatch():
    with pytest.raises(ValidationError):
        SignupForm(
            name="Test User",
            email="test@example.com",
            password="password123",
            password_confirm="different",
        )
    data = MultiDict()
    data.add("name", "Test User")
    data.add("email", "test@example.com")
    data.add("password", "password123")
    data.add("password_confirm", "password123")
    form, errors, _values = parse_form(SignupForm, data)
    assert errors == {}
    assert isinstance(form, SignupForm)


def test_signup_form_recaptcha_alias():
    data = MultiDict()
    data.add("name", "Test User")
    data.add("email", "test@example.com")
    data.add("password", "password123")
    data.add("password_confirm", "password123")
    data.add("g-recaptcha-response", "token-value")
    form, errors, _values = parse_form(SignupForm, data)
    assert errors == {}
    assert form is not None
    assert form.g_recaptcha_response == "token-value"


def test_forgot_password_form_parse():
    data = MultiDict()
    data.add("email", "a@example.com")
    form, errors, _values = parse_form(ForgotPasswordForm, data)
    assert errors == {}
    assert isinstance(form, ForgotPasswordForm)


def test_reset_password_form_mismatch():
    with pytest.raises(ValidationError):
        ResetPasswordForm(password="password123", password_confirm="x")


def test_reset_password_form_parse():
    data = MultiDict()
    data.add("password", "password123")
    data.add("password_confirm", "password123")
    form, errors, _values = parse_form(ResetPasswordForm, data)
    assert errors == {}
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

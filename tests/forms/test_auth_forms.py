"""Tests for auth forms"""

from datetime import datetime

import pytest

from app.forms.auth_forms import ForgotPasswordForm, LoginForm, SignupForm


class TestLoginForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = LoginForm(data={"email": "test@example.com", "password": "password123"})
            assert form.validate()

    def test_invalid_email(self, app):
        with app.test_request_context():
            form = LoginForm(data={"email": "invalid-email", "password": "password123"})
            assert not form.validate()


class TestSignupForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = SignupForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "1234567890",
                    "password": "password123",
                    "password_confirm": "password123",
                }
            )
            assert form.validate()

    def test_password_mismatch(self, app):
        with app.test_request_context():
            form = SignupForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "1234567890",
                    "password": "password123",
                    "password_confirm": "different",
                }
            )
            assert not form.validate()


class TestForgotPasswordForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = ForgotPasswordForm(data={"email": "test@example.com"})
            assert form.validate()

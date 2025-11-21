"""Tests for auth forms"""

import pytest
from app.forms.auth_forms import LoginForm, SignupForm, ForgotPasswordForm
from datetime import datetime


class TestLoginForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = LoginForm(
                data={"email": "test@example.com", "password": "password123"}
            )
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
                    "date_of_birth": datetime(2000, 1, 1).date(),
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
                    "date_of_birth": datetime(2000, 1, 1).date(),
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

from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, EmailStr, Field, field_validator


class CsrfForm(BaseModel):
    csrf_token: str = ""


class LoginForm(CsrfForm):
    email: EmailStr
    password: str


def login_form(
    csrf_token: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
) -> LoginForm:
    return LoginForm(csrf_token=csrf_token, email=email, password=password)


class SignupForm(CsrfForm):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = ""
    password: str = Field(min_length=8)
    password_confirm: str = ""
    qualification: str = "none"
    qualification_detail: str = ""
    g_recaptcha_response: str = ""

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if value != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return value


def signup_form(
    csrf_token: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    password_confirm: Annotated[str, Form()] = "",
    qualification: Annotated[str, Form()] = "none",
    qualification_detail: Annotated[str, Form()] = "",
    g_recaptcha_response: Annotated[str, Form(alias="g-recaptcha-response")] = "",
) -> SignupForm:
    return SignupForm(
        csrf_token=csrf_token,
        name=name,
        email=email,
        phone=phone or "",
        password=password,
        password_confirm=password_confirm,
        qualification=qualification,
        qualification_detail=qualification_detail,
        g_recaptcha_response=g_recaptcha_response,
    )


class ForgotPasswordForm(CsrfForm):
    email: EmailStr


def forgot_password_form(
    csrf_token: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
) -> ForgotPasswordForm:
    return ForgotPasswordForm(csrf_token=csrf_token, email=email)


class ResetPasswordForm(CsrfForm):
    password: str = Field(min_length=8)
    password_confirm: str = ""

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if value != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return value


def reset_password_form(
    csrf_token: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    password_confirm: Annotated[str, Form()] = "",
) -> ResetPasswordForm:
    return ResetPasswordForm(csrf_token=csrf_token, password=password, password_confirm=password_confirm)


class ProfileForm(CsrfForm):
    name: str = Field(min_length=2)
    phone: str = ""


class ChangePasswordForm(CsrfForm):
    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str = ""

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if value != info.data.get("new_password"):
            raise ValueError("New passwords do not match")
        return value

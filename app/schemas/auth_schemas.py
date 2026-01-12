from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class SignupSchema(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    password_confirm: str
    qualification: str = "none"

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v: str, info: Any) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    password: str = Field(min_length=8)
    password_confirm: str

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v: str, info: Any) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CsrfForm(BaseModel):
    csrf_token: str = ""


class LoginForm(CsrfForm):
    email: EmailStr
    password: str


class SignupForm(CsrfForm):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = ""
    password: str = Field(min_length=8)
    password_confirm: str = ""
    qualification: str = "none"
    qualification_detail: str = ""
    g_recaptcha_response: str = Field("", alias="g-recaptcha-response")

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if value != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return value


class ForgotPasswordForm(CsrfForm):
    email: EmailStr


class ResetPasswordForm(CsrfForm):
    password: str = Field(min_length=8)
    password_confirm: str = ""

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if value != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return value


class ProfileForm(CsrfForm):
    name: str = Field(min_length=2)
    phone: str = ""


class CreditsForm(CsrfForm):
    quantity: int = 1

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, value: object) -> object:
        if value is None or value == "":
            return 1
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError as exc:
                raise ValueError("Invalid quantity.") from exc
        raise ValueError("Invalid quantity.")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int) -> int:
        if value < 1 or value > 50:
            raise ValueError("Quantity must be between 1 and 50.")
        return value


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

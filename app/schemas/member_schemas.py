from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ProfileSchema(BaseModel):
    name: str = Field(min_length=2)
    phone: Optional[str] = None


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: Any) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v

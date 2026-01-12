"""Type-safe response models for service layer using Pydantic."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ServiceResponse(BaseModel, Generic[T]):
    """Generic service response with success/error handling."""

    success: bool
    data: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: T) -> "ServiceResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, error: str) -> "ServiceResponse[T]":
        """Create an error response."""
        return cls(success=False, data=None, error=error)


class UserCreationData(BaseModel):
    """Data for user creation result."""

    user_id: int
    email: str
    name: str
    is_active: bool


class MembershipUpdateData(BaseModel):
    """Data for membership update result."""

    user_id: int
    user_name: str
    credits: int | None = None
    expiry_date: str | None = None


class PasswordResetData(BaseModel):
    """Data for password reset result."""

    user_id: int
    email: str


class PaymentCheckoutData(BaseModel):
    """Data for payment checkout result."""

    checkout_id: str
    amount: float
    description: str


class ShootCreationData(BaseModel):
    """Data for shoot creation result."""

    shoot_id: int
    date: str
    location: str
    attendee_count: int
    warnings: list[str] = Field(default_factory=list)


class NewsArticleData(BaseModel):
    """Data for news article result."""

    article_id: int
    title: str
    published: bool


class EventData(BaseModel):
    """Data for event result."""

    event_id: int
    title: str
    start_date: str
    published: bool

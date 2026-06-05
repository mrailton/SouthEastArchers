from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.form_helpers import (
    coerce_bool,
    coerce_datetime,
    coerce_int_list,
    coerce_optional_date,
    coerce_optional_decimal,
)
from app.schemas.forms import CsrfForm

SHOOT_LOCATION_CHOICES: list[tuple[str, str]] = [
    ("HALL", "Hall"),
    ("MEADOW", "Meadow"),
    ("WOODS", "Woods"),
]

QUALIFICATION_CHOICES: list[tuple[str, str]] = [
    ("none", "None"),
    ("beginner", "Beginner Course Completed"),
    ("ai", "Archery Ireland Member"),
    ("ifaf", "Irish Field Archery Federation Member"),
]

EXPENSE_CATEGORY_CHOICES: list[tuple[str, str]] = [
    ("equipment", "Equipment"),
    ("venue_hire", "Venue Hire"),
    ("insurance", "Insurance"),
    ("supplies", "Supplies"),
    ("maintenance", "Maintenance"),
    ("travel", "Travel"),
    ("affiliation_fees", "Affiliation Fees"),
    ("coaching", "Coaching"),
    ("payment_processing_fees", "Payment Processing Fees"),
    ("other", "Other"),
]

INCOME_CATEGORY_CHOICES: list[tuple[str, str]] = [
    ("membership_fees", "Membership Fees"),
    ("shoot_fees", "Shoot Fees"),
    ("equipment_sales", "Equipment Sales"),
    ("donations", "Donations"),
    ("sponsorship", "Sponsorship"),
    ("grants", "Grants"),
    ("fundraising", "Fundraising"),
    ("other", "Other"),
]

SETTINGS_FIELD_DESCRIPTIONS: dict[str, str] = {
    "membership_year_start_month": "Month when membership year starts (1-12)",
    "membership_year_start_day": "Day when membership year starts (1-31)",
    "annual_membership_cost": "Cost in euros (e.g., 100 for €100)",
    "membership_shoots_included": "Number of shoots included with membership",
    "additional_shoot_cost": "Cost per additional shoot in euros",
    "visitor_shoot_fee": "Fee per shoot for visiting non-member archers",
    "cash_payment_instructions": "Instructions shown to users when they select cash payment",
    "sumup_fee_percentage": "SumUp transaction fee percentage (e.g., 2.50 for 2.5%). Leave blank to disable automatic transaction recording.",
}


class ShootForm(CsrfForm):
    date: date
    location: Literal["HALL", "MEADOW", "WOODS"]
    description: str = ""
    attendees: list[int] = Field(default_factory=list)

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        parsed = coerce_optional_date(value)
        if parsed is None:
            raise ValueError("Date is required.")
        return parsed

    @field_validator("attendees", mode="before")
    @classmethod
    def parse_attendees(cls, value: object) -> list[int]:
        return coerce_int_list(value)


class NewsForm(CsrfForm):
    title: str = Field(min_length=5)
    summary: str = ""
    content: str = Field(min_length=20)
    published: bool = False

    @field_validator("published", mode="before")
    @classmethod
    def parse_published(cls, value: object) -> bool:
        return coerce_bool(value)


class EventForm(CsrfForm):
    title: str = Field(min_length=5)
    description: str = Field(min_length=1)
    start_date: datetime
    location: str = ""
    published: bool = False

    @field_validator("start_date", mode="before")
    @classmethod
    def parse_start_date(cls, value: object) -> datetime:
        return coerce_datetime(value)

    @field_validator("published", mode="before")
    @classmethod
    def parse_published(cls, value: object) -> bool:
        return coerce_bool(value)


class CreateMemberForm(CsrfForm):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = ""
    password: str = ""
    roles: list[int] = Field(default_factory=list)
    create_membership: bool = False

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, value: object) -> list[int]:
        return coerce_int_list(value)

    @field_validator("create_membership", mode="before")
    @classmethod
    def parse_create_membership(cls, value: object) -> bool:
        return coerce_bool(value)


class EditMemberForm(CsrfForm):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = ""
    qualification: Literal["none", "beginner", "ai", "ifaf"] = "none"
    qualification_detail: str = ""
    password: str = ""
    roles: list[int] = Field(default_factory=list)
    is_active: bool = True
    membership_start_date: date | None = None
    membership_expiry_date: date | None = None
    membership_initial_credits: int | None = None
    membership_purchased_credits: int | None = None

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, value: object) -> list[int]:
        return coerce_int_list(value)

    @field_validator("is_active", mode="before")
    @classmethod
    def parse_is_active(cls, value: object) -> bool:
        return coerce_bool(value)

    @field_validator(
        "membership_start_date",
        "membership_expiry_date",
        mode="before",
    )
    @classmethod
    def parse_optional_dates(cls, value: object) -> date | None:
        return coerce_optional_date(value)

    @field_validator("membership_initial_credits", "membership_purchased_credits", mode="before")
    @classmethod
    def parse_optional_int(cls, value: object) -> int | None:
        if value is None or value == "":
            return None
        return int(value)


class SettingsForm(CsrfForm):
    membership_year_start_month: int = Field(ge=1, le=12)
    membership_year_start_day: int = Field(ge=1, le=31)
    annual_membership_cost: int = Field(ge=0)
    membership_shoots_included: int = Field(ge=0)
    additional_shoot_cost: int = Field(ge=0)
    visitor_shoot_fee: int = Field(ge=0)
    cash_payment_instructions: str = Field(min_length=10, max_length=1000)
    sumup_fee_percentage: Decimal | None = None
    news_enabled: bool = False
    events_enabled: bool = False

    @field_validator("sumup_fee_percentage", mode="before")
    @classmethod
    def parse_sumup_fee(cls, value: object) -> Decimal | None:
        return coerce_optional_decimal(value)

    @field_validator("news_enabled", "events_enabled", mode="before")
    @classmethod
    def parse_feature_flags(cls, value: object) -> bool:
        return coerce_bool(value)


class RoleForm(CsrfForm):
    name: str = Field(min_length=2, max_length=64)
    description: str = Field(default="", max_length=255)
    permissions: list[int] = Field(default_factory=list)

    @field_validator("permissions", mode="before")
    @classmethod
    def parse_permissions(cls, value: object) -> list[int]:
        return coerce_int_list(value)


class ExpenseForm(CsrfForm):
    date: date
    amount: Decimal = Field(gt=0)
    category: str
    description: str = Field(min_length=3)
    receipt_reference: str = ""

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        parsed = coerce_optional_date(value)
        if parsed is None:
            raise ValueError("Date is required.")
        return parsed

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        parsed = coerce_optional_decimal(value)
        if parsed is None:
            raise ValueError("Amount is required.")
        return parsed


class IncomeForm(CsrfForm):
    date: date
    amount: Decimal = Field(gt=0)
    category: str
    description: str = Field(min_length=3)
    source: str = ""

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        parsed = coerce_optional_date(value)
        if parsed is None:
            raise ValueError("Date is required.")
        return parsed

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        parsed = coerce_optional_decimal(value)
        if parsed is None:
            raise ValueError("Amount is required.")
        return parsed


class FinancialStatementForm(CsrfForm):
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        parsed = coerce_optional_date(value)
        if parsed is None:
            raise ValueError("Date is required.")
        return parsed

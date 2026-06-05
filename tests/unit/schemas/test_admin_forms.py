from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.admin_forms import (
    CreateMemberForm,
    EditMemberForm,
    EventForm,
    ExpenseForm,
    FinancialStatementForm,
    IncomeForm,
    NewsForm,
    RoleForm,
    SettingsForm,
    ShootForm,
)


def test_shoot_form_requires_date():
    with pytest.raises(ValidationError):
        ShootForm.model_validate({"date": "", "location": "HALL"})


def test_shoot_form_parses_attendees_list():
    form = ShootForm.model_validate({"date": "2026-03-01", "location": "HALL", "attendees": ["1", "2"]})
    assert form.attendees == [1, 2]


def test_news_form_published_checkbox():
    form = NewsForm.model_validate(
        {
            "title": "Long enough title",
            "content": "Enough content for the article body here.",
            "published": "on",
        }
    )
    assert form.published is True


def test_event_form_datetime():
    form = EventForm.model_validate(
        {
            "title": "Long enough title",
            "description": "Desc",
            "start_date": "2026-03-01T10:00",
        }
    )
    assert form.start_date.year == 2026


def test_create_member_form_roles_and_membership_flag():
    form = CreateMemberForm.model_validate(
        {
            "name": "New Member",
            "email": "new@example.com",
            "roles": "3",
            "create_membership": "true",
        }
    )
    assert form.roles == [3]
    assert form.create_membership is True


def test_edit_member_optional_int_and_dates():
    form = EditMemberForm.model_validate(
        {
            "name": "Member",
            "email": "m@example.com",
            "membership_start_date": "2026-01-01",
            "membership_initial_credits": "5",
        }
    )
    assert form.membership_start_date == date(2026, 1, 1)
    assert form.membership_initial_credits == 5


def test_settings_form_sumup_fee_optional():
    form = SettingsForm.model_validate(
        {
            "membership_year_start_month": "4",
            "membership_year_start_day": "1",
            "annual_membership_cost": "100",
            "membership_shoots_included": "20",
            "additional_shoot_cost": "5",
            "visitor_shoot_fee": "8",
            "cash_payment_instructions": "Pay at the club on shoot night please.",
            "sumup_fee_percentage": "",
        }
    )
    assert form.sumup_fee_percentage is None


def test_role_form_permissions():
    form = RoleForm.model_validate({"name": "Custom", "permissions": ["1", "2"]})
    assert form.permissions == [1, 2]


def test_expense_form_requires_amount():
    with pytest.raises(ValidationError):
        ExpenseForm.model_validate(
            {
                "date": "2026-01-01",
                "amount": "",
                "category": "equipment",
                "description": "Test expense",
            }
        )


def test_income_form_amount_decimal():
    form = IncomeForm.model_validate(
        {
            "date": "2026-01-01",
            "amount": "25.50",
            "category": "donations",
            "description": "Donation received",
        }
    )
    assert form.amount == Decimal("25.50")


def test_financial_statement_form_dates():
    form = FinancialStatementForm.model_validate({"start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert form.end_date == date(2026, 1, 31)

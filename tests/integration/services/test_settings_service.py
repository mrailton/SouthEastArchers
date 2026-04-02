from datetime import date, datetime
from decimal import Decimal

import pytest

from app.services.settings_service import SettingsService


def test_get_returns_default_when_not_set(app):
    """Test that get() returns the registered default when no row exists"""
    assert SettingsService.get("membership_year_start_month") == 3
    assert SettingsService.get("membership_year_start_day") == 1
    assert SettingsService.get("annual_membership_cost") == 10000
    assert SettingsService.get("membership_shoots_included") == 20
    assert SettingsService.get("additional_shoot_cost") == 500


def test_get_returns_stored_value(app):
    """Test that get() returns a previously stored value"""
    SettingsService.set("membership_year_start_month", 6)
    assert SettingsService.get("membership_year_start_month") == 6


def test_get_unknown_key_raises(app):
    """Test that get() raises KeyError for an unknown setting key"""
    with pytest.raises(KeyError, match="Unknown setting"):
        SettingsService.get("nonexistent_key")


def test_set_and_get_roundtrip(app):
    """Test that set() persists and get() reads back correctly"""
    SettingsService.set("annual_membership_cost", 15000)
    assert SettingsService.get("annual_membership_cost") == 15000


def test_set_overwrites_existing(app):
    """Test that set() overwrites a previously stored value"""
    SettingsService.set("membership_year_start_month", 9)
    SettingsService.set("membership_year_start_month", 12)
    assert SettingsService.get("membership_year_start_month") == 12


def test_get_all_returns_typed_dict(app):
    """Test that get_all() returns all settings with correct types"""
    all_settings = SettingsService.get_all()

    assert isinstance(all_settings, dict)
    assert all_settings["membership_year_start_month"] == 3
    assert all_settings["news_enabled"] is False
    assert all_settings["sumup_fee_percentage"] is None
    assert isinstance(all_settings["cash_payment_instructions"], str)


def test_get_all_includes_stored_values(app):
    """Test that get_all() reflects stored values"""
    SettingsService.set("news_enabled", True)
    SettingsService.set("annual_membership_cost", 20000)

    all_settings = SettingsService.get_all()
    assert all_settings["news_enabled"] is True
    assert all_settings["annual_membership_cost"] == 20000


def test_save_many(app):
    """Test bulk-saving multiple settings"""
    SettingsService.save_many(
        {
            "membership_year_start_month": 9,
            "membership_year_start_day": 15,
            "annual_membership_cost": 20000,
            "membership_shoots_included": 30,
            "additional_shoot_cost": 1000,
        }
    )

    assert SettingsService.get("membership_year_start_month") == 9
    assert SettingsService.get("membership_year_start_day") == 15
    assert SettingsService.get("annual_membership_cost") == 20000
    assert SettingsService.get("membership_shoots_included") == 30
    assert SettingsService.get("additional_shoot_cost") == 1000


def test_bool_serialization(app):
    """Test that boolean settings serialize and deserialize correctly"""
    SettingsService.set("news_enabled", True)
    assert SettingsService.get("news_enabled") is True

    SettingsService.set("news_enabled", False)
    assert SettingsService.get("news_enabled") is False


def test_decimal_serialization(app):
    """Test that decimal settings serialize and deserialize correctly"""
    SettingsService.set("sumup_fee_percentage", Decimal("2.50"))
    result = SettingsService.get("sumup_fee_percentage")
    assert result == Decimal("2.50")


def test_decimal_none_default(app):
    """Test that sumup_fee_percentage defaults to None"""
    assert SettingsService.get("sumup_fee_percentage") is None


def test_calculate_membership_expiry_before_year_start(app):
    """Test expiry calculation when signing up before year start date"""
    # Default settings: March 1
    start_date = date(2026, 1, 15)
    expiry = SettingsService.calculate_membership_expiry(start_date)

    assert expiry.date() == date(2026, 2, 28)
    assert expiry.hour == 23
    assert expiry.minute == 59
    assert expiry.second == 59


def test_calculate_membership_expiry_after_year_start(app):
    """Test expiry calculation when signing up after year start date"""
    start_date = date(2026, 4, 15)
    expiry = SettingsService.calculate_membership_expiry(start_date)

    assert expiry.date() == date(2027, 2, 28)
    assert expiry.hour == 23
    assert expiry.minute == 59
    assert expiry.second == 59


def test_calculate_membership_expiry_on_year_start_date(app):
    """Test expiry calculation when signing up ON the year start date"""
    start_date = date(2026, 3, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date)

    assert expiry.date() == date(2027, 2, 28)


def test_calculate_membership_expiry_with_datetime(app):
    """Test that calculate_membership_expiry accepts datetime objects"""
    start_datetime = datetime(2026, 1, 15, 10, 30, 0)
    expiry = SettingsService.calculate_membership_expiry(start_datetime)

    assert expiry.date() == date(2026, 2, 28)


def test_calculate_membership_expiry_leap_year(app):
    """Test expiry calculation accounts for leap years"""
    start_date = date(2027, 6, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date)

    assert expiry.date() == date(2028, 2, 29)


def test_calculate_membership_expiry_custom_start(app):
    """Test expiry calculation with non-default membership year start"""
    SettingsService.set("membership_year_start_month", 6)
    SettingsService.set("membership_year_start_day", 15)

    # Before June 15 → expires June 14
    start_date = date(2026, 4, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date)
    assert expiry.date() == date(2026, 6, 14)

    # After June 15 → expires June 14 next year
    start_date = date(2026, 7, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date)
    assert expiry.date() == date(2027, 6, 14)


def test_membership_expiry_edge_cases(app):
    """Test edge cases for membership expiry calculation"""
    # Case 1: Purchase on Feb 28 (day before year starts) → expires Feb 28
    start = date(2026, 2, 28)
    expiry = SettingsService.calculate_membership_expiry(start)
    assert expiry.date() == date(2026, 2, 28)

    # Case 2: Purchase on March 1 (year start day) → expires Feb 28 next year
    start = date(2026, 3, 1)
    expiry = SettingsService.calculate_membership_expiry(start)
    assert expiry.date() == date(2027, 2, 28)

    # Case 3: Purchase on March 2 (day after year starts) → expires Feb 28 next year
    start = date(2026, 3, 2)
    expiry = SettingsService.calculate_membership_expiry(start)
    assert expiry.date() == date(2027, 2, 28)

    # Case 4: Purchase on Dec 31 (late in year) → expires Feb 28 next year
    start = date(2026, 12, 31)
    expiry = SettingsService.calculate_membership_expiry(start)
    assert expiry.date() == date(2027, 2, 28)

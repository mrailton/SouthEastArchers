"""Tests for SettingsService"""

from datetime import date, datetime

from app import db
from app.models import ApplicationSettings
from app.services.settings_service import SettingsService


def test_get_creates_settings_if_not_exists(app):
    """Test that get() creates default settings if they don't exist"""
    settings = SettingsService.get()

    assert settings is not None
    assert settings.membership_year_start_month == 3
    assert settings.membership_year_start_day == 1
    assert settings.annual_membership_cost == 10000
    assert settings.membership_shoots_included == 20
    assert settings.additional_shoot_cost == 500


def test_get_returns_existing_settings(app):
    """Test that get() returns existing settings"""
    # Create settings
    existing = ApplicationSettings(
        membership_year_start_month=6,
        membership_year_start_day=15,
        annual_membership_cost=15000,
        membership_shoots_included=25,
        additional_shoot_cost=600,
    )
    db.session.add(existing)
    db.session.commit()

    settings = SettingsService.get()

    assert settings.membership_year_start_month == 6
    assert settings.membership_year_start_day == 15
    assert settings.annual_membership_cost == 15000
    assert settings.membership_shoots_included == 25
    assert settings.additional_shoot_cost == 600


def test_save_updates_settings(app):
    """Test that save() persists changes to settings"""
    settings = SettingsService.get()

    settings.membership_year_start_month = 9
    settings.annual_membership_cost = 12000

    SettingsService.save(settings)

    # Fetch fresh from database
    db.session.expire_all()
    updated = SettingsService.get()

    assert updated.membership_year_start_month == 9
    assert updated.annual_membership_cost == 12000


def test_calculate_membership_expiry_before_year_start(app):
    """Test expiry calculation when signing up before year start date"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3  # March
    settings.membership_year_start_day = 1

    # Sign up on January 15, 2026 (before March 1, 2026)
    start_date = date(2026, 1, 15)
    expiry = SettingsService.calculate_membership_expiry(start_date, settings)

    # Should expire Feb 28, 2026 23:59:59 (day before March 1, 2026)
    assert expiry.date() == date(2026, 2, 28)
    assert expiry.hour == 23
    assert expiry.minute == 59
    assert expiry.second == 59


def test_calculate_membership_expiry_after_year_start(app):
    """Test expiry calculation when signing up after year start date"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3  # March
    settings.membership_year_start_day = 1

    # Sign up on April 15, 2026
    start_date = date(2026, 4, 15)
    expiry = SettingsService.calculate_membership_expiry(start_date, settings)

    # Should expire Feb 28, 2027 23:59:59 (day before March 1, 2027)
    assert expiry.date() == date(2027, 2, 28)
    assert expiry.hour == 23
    assert expiry.minute == 59
    assert expiry.second == 59


def test_calculate_membership_expiry_on_year_start_date(app):
    """Test expiry calculation when signing up ON the year start date"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3  # March
    settings.membership_year_start_day = 1

    # Sign up on March 1, 2026
    start_date = date(2026, 3, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date, settings)

    # Should expire Feb 28, 2027 23:59:59 (full year)
    assert expiry.date() == date(2027, 2, 28)


def test_calculate_membership_expiry_with_datetime(app):
    """Test that calculate_membership_expiry accepts datetime objects"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3
    settings.membership_year_start_day = 1

    # Pass datetime instead of date (Jan 15, 2026 - before March 1)
    start_datetime = datetime(2026, 1, 15, 10, 30, 0)
    expiry = SettingsService.calculate_membership_expiry(start_datetime, settings)

    # Should expire Feb 28, 2026 (before the year start)
    assert expiry.date() == date(2026, 2, 28)


def test_calculate_membership_expiry_leap_year(app):
    """Test expiry calculation accounts for leap years"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3
    settings.membership_year_start_day = 1

    # Sign up in 2027 (not leap), expires before 2028 (leap)
    start_date = date(2027, 6, 1)
    expiry = SettingsService.calculate_membership_expiry(start_date, settings)

    # Should expire Feb 29, 2028 23:59:59 (leap year)
    assert expiry.date() == date(2028, 2, 29)


def test_calculate_membership_expiry_without_settings_arg(app):
    """Test that calculate_membership_expiry fetches settings if not provided"""
    # Don't pass settings argument
    start_date = date(2026, 1, 15)
    expiry = SettingsService.calculate_membership_expiry(start_date)

    # Should use default settings (March 1 start)
    # Jan 15 is before March 1, so expires Feb 28, 2026
    assert expiry.date() == date(2026, 2, 28)


def test_singleton_pattern_only_one_record(app):
    """Test that only one settings record exists"""
    settings1 = SettingsService.get()
    settings2 = SettingsService.get()

    # Should be the same record
    assert settings1.id == settings2.id

    # Should only have one record total
    count = ApplicationSettings.query.count()
    assert count == 1


def test_default_values_are_correct(app):
    """Test that default values match expectations"""
    settings = SettingsService.get()

    assert settings.membership_year_start_month == 3
    assert settings.membership_year_start_day == 1
    assert settings.annual_membership_cost == 10000  # €100 in cents
    assert settings.membership_shoots_included == 20
    assert settings.additional_shoot_cost == 500  # €5 in cents


def test_settings_have_timestamps(app):
    """Test that settings have created_at and updated_at timestamps"""
    settings = SettingsService.get()

    assert settings.created_at is not None
    assert settings.updated_at is not None
    assert isinstance(settings.created_at, datetime)
    assert isinstance(settings.updated_at, datetime)


def test_update_all_fields(app):
    """Test that all fields can be updated"""
    settings = SettingsService.get()

    settings.membership_year_start_month = 9
    settings.membership_year_start_day = 15
    settings.annual_membership_cost = 20000
    settings.membership_shoots_included = 30
    settings.additional_shoot_cost = 1000

    SettingsService.save(settings)

    # Verify all updates
    db.session.expire_all()
    updated = SettingsService.get()

    assert updated.membership_year_start_month == 9
    assert updated.membership_year_start_day == 15
    assert updated.annual_membership_cost == 20000
    assert updated.membership_shoots_included == 30
    assert updated.additional_shoot_cost == 1000


def test_membership_expiry_edge_cases(app):
    """Test edge cases for membership expiry calculation"""
    settings = SettingsService.get()
    settings.membership_year_start_month = 3  # March
    settings.membership_year_start_day = 1

    # Case 1: Purchase on Feb 28 (day before year starts) → expires Feb 28
    start = date(2026, 2, 28)
    expiry = SettingsService.calculate_membership_expiry(start, settings)
    assert expiry.date() == date(2026, 2, 28)

    # Case 2: Purchase on March 1 (year start day) → expires Feb 28 next year
    start = date(2026, 3, 1)
    expiry = SettingsService.calculate_membership_expiry(start, settings)
    assert expiry.date() == date(2027, 2, 28)

    # Case 3: Purchase on March 2 (day after year starts) → expires Feb 28 next year
    start = date(2026, 3, 2)
    expiry = SettingsService.calculate_membership_expiry(start, settings)
    assert expiry.date() == date(2027, 2, 28)

    # Case 4: Purchase on Dec 31 (late in year) → expires Feb 28 next year
    start = date(2026, 12, 31)
    expiry = SettingsService.calculate_membership_expiry(start, settings)
    assert expiry.date() == date(2027, 2, 28)

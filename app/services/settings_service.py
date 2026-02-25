from datetime import datetime, timedelta

from app.models.application_settings import ApplicationSettings
from app.repositories import SettingsRepository


class SettingsService:
    """Service for managing application settings (singleton pattern)."""

    @staticmethod
    def get() -> ApplicationSettings:
        """Get the application settings (creates with defaults if doesn't exist)."""
        settings = SettingsRepository.get()
        if not settings:
            settings = ApplicationSettings()
            SettingsRepository.add(settings)
            SettingsRepository.save()
        return settings

    @staticmethod
    def save(settings: ApplicationSettings) -> ApplicationSettings:
        """Save application settings."""
        SettingsRepository.save()
        return settings

    @staticmethod
    def calculate_membership_expiry(start_date, settings: ApplicationSettings | None = None) -> datetime:
        """Calculate membership expiry date based on start date and settings.

        The expiry is 23:59:59 on the day before the next membership year starts.
        For example, if membership year starts March 1st:
        - Membership starting 2026-01-15 expires 2026-02-28 23:59:59 (before year start)
        - Membership starting 2026-03-15 expires 2027-02-28 23:59:59 (after year start)
        - Membership starting 2026-12-31 expires 2027-02-28 23:59:59 (after year start)

        Args:
            start_date: The membership start date (date or datetime)
            settings: Optional settings instance (fetched if not provided)

        Returns:
            The membership expiry datetime
        """

        if settings is None:
            settings = SettingsService.get()

        # Convert to date if datetime
        if isinstance(start_date, datetime):
            start_date = start_date.date()

        # Find this year's membership year start date
        year = start_date.year
        this_year_start = datetime(
            year,
            settings.membership_year_start_month,
            settings.membership_year_start_day,
            0,
            0,
            0,
        )

        # If purchasing before this year's membership year starts,
        # membership expires the day before this year starts
        if start_date < this_year_start.date():
            expiry = this_year_start - timedelta(seconds=1)
        else:
            # Otherwise, membership expires the day before next year starts
            next_year_start = datetime(
                year + 1,
                settings.membership_year_start_month,
                settings.membership_year_start_day,
                0,
                0,
                0,
            )
            expiry = next_year_start - timedelta(seconds=1)

        return expiry

"""Service layer for application settings (key-value store)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from app.repositories import SettingsRepository

# ---------------------------------------------------------------------------
# Setting definitions — each key's value type and default.
# Monetary values are stored in cents (integers) to avoid floating-point issues.
# ---------------------------------------------------------------------------
SETTING_DEFINITIONS: dict[str, dict[str, Any]] = {
    "membership_year_start_month": {"type": "int", "default": 3},
    "membership_year_start_day": {"type": "int", "default": 1},
    "annual_membership_cost": {"type": "int", "default": 10000},
    "membership_shoots_included": {"type": "int", "default": 20},
    "additional_shoot_cost": {"type": "int", "default": 500},
    "visitor_shoot_fee": {"type": "int", "default": 1000},
    "news_enabled": {"type": "bool", "default": False},
    "events_enabled": {"type": "bool", "default": False},
    "cash_payment_instructions": {
        "type": "str",
        "default": (
            "Please pay cash to a committee member at the next shoot night. "
            "Your membership/credits will be activated once payment is confirmed."
        ),
    },
    "sumup_fee_percentage": {"type": "decimal", "default": None},
}


def _deserialize(raw: str | None, value_type: str, default: Any) -> Any:
    """Convert a raw DB string to the correct Python type."""
    if raw is None:
        return default
    if value_type == "int":
        return int(raw)
    if value_type == "bool":
        return raw.lower() in ("true", "1", "yes")
    if value_type == "str":
        return raw
    if value_type == "decimal":
        try:
            return Decimal(raw)
        except InvalidOperation:
            return default
    return raw


def _serialize(value: Any, value_type: str) -> str | None:
    """Convert a Python value to its raw DB string."""
    if value is None:
        return None
    if value_type == "bool":
        return "true" if value else "false"
    return str(value)


class SettingsService:
    """Service for managing application settings (key-value store)."""

    @staticmethod
    def get(key: str) -> Any:
        """Get a typed setting value by key, falling back to the registered default."""
        definition = SETTING_DEFINITIONS.get(key)
        if not definition:
            raise KeyError(f"Unknown setting: {key}")
        raw = SettingsRepository.get_value(key)
        return _deserialize(raw, definition["type"], definition["default"])

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a single setting value and commit."""
        definition = SETTING_DEFINITIONS.get(key)
        if not definition:
            raise KeyError(f"Unknown setting: {key}")
        raw = _serialize(value, definition["type"])
        SettingsRepository.set_value(key, raw)
        SettingsRepository.save()

    @staticmethod
    def get_all() -> dict[str, Any]:
        """Get all settings as a typed dict."""
        stored = SettingsRepository.get_all()
        result: dict[str, Any] = {}
        for key, definition in SETTING_DEFINITIONS.items():
            raw = stored.get(key)
            result[key] = _deserialize(raw, definition["type"], definition["default"])
        return result

    @staticmethod
    def save_many(mapping: dict[str, Any]) -> None:
        """Bulk-save multiple settings in one commit."""
        for key, value in mapping.items():
            definition = SETTING_DEFINITIONS.get(key)
            if not definition:
                raise KeyError(f"Unknown setting: {key}")
            raw = _serialize(value, definition["type"])
            SettingsRepository.set_value(key, raw)
        SettingsRepository.save()

    @staticmethod
    def calculate_membership_expiry(start_date: date | datetime) -> datetime:
        """Calculate membership expiry date based on start date and settings.

        The expiry is 23:59:59 on the day before the next membership year starts.
        For example, if membership year starts March 1st:
        - Membership starting 2026-01-15 expires 2026-02-28 23:59:59 (before year start)
        - Membership starting 2026-03-15 expires 2027-02-28 23:59:59 (after year start)
        - Membership starting 2026-12-31 expires 2027-02-28 23:59:59 (after year start)

        Args:
            start_date: The membership start date (date or datetime)

        Returns:
            The membership expiry datetime
        """
        if isinstance(start_date, datetime):
            start_date = start_date.date()

        year = start_date.year
        start_month: int = SettingsService.get("membership_year_start_month")
        start_day: int = SettingsService.get("membership_year_start_day")

        this_year_start = datetime(year, start_month, start_day, 0, 0, 0)

        if start_date < this_year_start.date():
            expiry = this_year_start - timedelta(seconds=1)
        else:
            next_year_start = datetime(year + 1, start_month, start_day, 0, 0, 0)
            expiry = next_year_start - timedelta(seconds=1)

        return expiry

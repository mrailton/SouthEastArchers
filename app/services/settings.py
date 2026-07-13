"""Service layer for application settings (key-value store)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from app.repositories import SettingsRepository


# ---------------------------------------------------------------------------
# Setting definitions — each key's value type and default.
# Monetary values are stored in cents (integers) to avoid floating-point issues.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SettingDef:
    type: str
    default: Any


SETTING_DEFINITIONS: dict[str, SettingDef] = {
    "membership_year_start_month": SettingDef(type="int", default=3),
    "membership_year_start_day": SettingDef(type="int", default=1),
    "annual_membership_cost": SettingDef(type="int", default=10000),
    "membership_shoots_included": SettingDef(type="int", default=20),
    "additional_shoot_cost": SettingDef(type="int", default=500),
    "visitor_shoot_fee": SettingDef(type="int", default=1000),
    "news_enabled": SettingDef(type="bool", default=False),
    "events_enabled": SettingDef(type="bool", default=False),
    "cash_payment_instructions": SettingDef(
        type="str",
        default="Please pay cash to a committee member at the next shoot night. Your membership/credits will be activated once payment is confirmed.",
    ),
    "sumup_fee_percentage": SettingDef(type="decimal", default=None),
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


def get(key: str) -> Any:
    definition = SETTING_DEFINITIONS.get(key)
    if not definition:
        raise KeyError(f"Unknown setting: {key}")
    raw = SettingsRepository.get_value(key)
    return _deserialize(raw, definition.type, definition.default)


def set(key: str, value: Any) -> None:
    definition = SETTING_DEFINITIONS.get(key)
    if not definition:
        raise KeyError(f"Unknown setting: {key}")
    raw = _serialize(value, definition.type)
    SettingsRepository.set_value(key, raw)
    SettingsRepository.save()


def get_all() -> dict[str, Any]:
    stored = SettingsRepository.get_all()
    result: dict[str, Any] = {}
    for key, definition in SETTING_DEFINITIONS.items():
        raw = stored.get(key)
        result[key] = _deserialize(raw, definition.type, definition.default)
    return result


def save_many(mapping: dict[str, Any]) -> None:
    for key, value in mapping.items():
        definition = SETTING_DEFINITIONS.get(key)
        if not definition:
            raise KeyError(f"Unknown setting: {key}")
        raw = _serialize(value, definition.type)
        SettingsRepository.set_value(key, raw)
    SettingsRepository.save()


def calculate_membership_expiry(start_date: date | datetime) -> datetime:
    if isinstance(start_date, datetime):
        start_date = start_date.date()

    year = start_date.year
    start_month: int = get("membership_year_start_month")
    start_day: int = get("membership_year_start_day")

    this_year_start = datetime(year, start_month, start_day, 0, 0, 0)

    if start_date < this_year_start.date():
        expiry = this_year_start - timedelta(seconds=1)
    else:
        next_year_start = datetime(year + 1, start_month, start_day, 0, 0, 0)
        expiry = next_year_start - timedelta(seconds=1)

    return expiry


def get_membership_year_start(today: date | None = None) -> date:
    """Return the start date of the current membership year.

    Uses ``membership_year_start_month`` and ``membership_year_start_day``
    from settings. If today falls before the configured month/day, the year
    start is in the previous calendar year.
    """
    if today is None:
        today = date.today()
    start_month: int = get("membership_year_start_month")
    start_day: int = get("membership_year_start_day")
    this_year_start = date(today.year, start_month, start_day)
    if today >= this_year_start:
        return this_year_start
    return date(today.year - 1, start_month, start_day)

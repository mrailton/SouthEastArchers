from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.settings_service import SETTING_DEFINITIONS, _deserialize


def get_setting(db: Session | None, key: str):
    definition = SETTING_DEFINITIONS.get(key)
    if not definition:
        raise KeyError(f"Unknown setting: {key}")
    if db is None:
        return definition.default
    raw = db.execute(text("SELECT value FROM setting WHERE `key` = :key"), {"key": key}).scalar()
    return _deserialize(raw, definition.type, definition.default)


def calculate_membership_expiry(db: Session, start_date: date | datetime) -> datetime:
    if isinstance(start_date, datetime):
        start_date = start_date.date()

    year = start_date.year
    start_month: int = get_setting(db, "membership_year_start_month")
    start_day: int = get_setting(db, "membership_year_start_day")

    this_year_start = datetime(year, start_month, start_day, 0, 0, 0)
    if start_date < this_year_start.date():
        return this_year_start - timedelta(seconds=1)

    next_year_start = datetime(year + 1, start_month, start_day, 0, 0, 0)
    return next_year_start - timedelta(seconds=1)

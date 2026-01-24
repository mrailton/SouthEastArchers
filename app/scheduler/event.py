from collections.abc import Callable
from datetime import datetime


class Event:
    """Represents a scheduled task event."""

    def __init__(self, callback: Callable, description: str = ""):
        self.callback = callback
        self.description = description or getattr(callback, "__name__", "")
        self.expression = "* * * * *"  # Default: every minute
        self._timezone = None
        self._when = None
        self._filters = []  # Filters that take datetime
        self._filters_no_arg = []  # Filters that don't take arguments (for when/skip)
        self._rejects = []

    def cron(self, expression: str) -> Event:
        """Set a custom cron expression."""
        self.expression = expression
        return self

    def hourly(self) -> Event:
        """Schedule task to run every hour."""
        return self.cron("0 * * * *")

    def hourly_at(self, minute: int) -> Event:
        """Schedule task to run every hour at specific minute."""
        return self.cron(f"{minute} * * * *")

    def daily(self) -> Event:
        """Schedule task to run daily at midnight."""
        return self.cron("0 0 * * *")

    def daily_at(self, time_str: str) -> Event:
        """Schedule task to run daily at specific time (HH:MM format)."""
        hour, minute = time_str.split(":")
        return self.cron(f"{minute} {hour} * * *")

    def weekly(self) -> Event:
        """Schedule task to run weekly on Sunday at midnight."""
        return self.cron("0 0 * * 0")

    def weekly_on(self, day: int, time_str: str = "00:00") -> Event:
        """Schedule task to run weekly on specific day (0=Sunday) at specific time."""
        hour, minute = time_str.split(":")
        return self.cron(f"{int(minute)} {int(hour)} * * {day}")

    def monthly(self) -> Event:
        """Schedule task to run monthly on the first day at midnight."""
        return self.cron("0 0 1 * *")

    def monthly_on(self, day: int, time_str: str = "00:00") -> Event:
        """Schedule task to run monthly on specific day at specific time."""
        hour, minute = time_str.split(":")
        return self.cron(f"{int(minute)} {int(hour)} {day} * *")

    def yearly(self) -> Event:
        """Schedule task to run yearly on January 1st at midnight."""
        return self.cron("0 0 1 1 *")

    def every_minute(self) -> Event:
        """Schedule task to run every minute."""
        return self.cron("* * * * *")

    def every_five_minutes(self) -> Event:
        """Schedule task to run every 5 minutes."""
        return self.cron("*/5 * * * *")

    def every_ten_minutes(self) -> Event:
        """Schedule task to run every 10 minutes."""
        return self.cron("*/10 * * * *")

    def every_fifteen_minutes(self) -> Event:
        """Schedule task to run every 15 minutes."""
        return self.cron("*/15 * * * *")

    def every_thirty_minutes(self) -> Event:
        """Schedule task to run every 30 minutes."""
        return self.cron("*/30 * * * *")

    def weekdays(self) -> Event:
        """Constrain task to run only on weekdays."""
        self._filters.append(lambda dt: dt.weekday() < 5)
        return self

    def weekends(self) -> Event:
        """Constrain task to run only on weekends."""
        self._filters.append(lambda dt: dt.weekday() >= 5)
        return self

    def mondays(self) -> Event:
        """Constrain task to run only on Mondays."""
        self._filters.append(lambda dt: dt.weekday() == 0)
        return self

    def tuesdays(self) -> Event:
        """Constrain task to run only on Tuesdays."""
        self._filters.append(lambda dt: dt.weekday() == 1)
        return self

    def wednesdays(self) -> Event:
        """Constrain task to run only on Wednesdays."""
        self._filters.append(lambda dt: dt.weekday() == 2)
        return self

    def thursdays(self) -> Event:
        """Constrain task to run only on Thursdays."""
        self._filters.append(lambda dt: dt.weekday() == 3)
        return self

    def fridays(self) -> Event:
        """Constrain task to run only on Fridays."""
        self._filters.append(lambda dt: dt.weekday() == 4)
        return self

    def saturdays(self) -> Event:
        """Constrain task to run only on Saturdays."""
        self._filters.append(lambda dt: dt.weekday() == 5)
        return self

    def sundays(self) -> Event:
        """Constrain task to run only on Sundays."""
        self._filters.append(lambda dt: dt.weekday() == 6)
        return self

    def when(self, callback: Callable[[], bool]) -> Event:
        """Constrain task based on a truth test."""
        self._filters_no_arg.append(callback)
        return self

    def skip(self, callback: Callable[[], bool]) -> Event:
        """Skip task based on a truth test."""
        self._rejects.append(callback)
        return self

    def is_due(self, now: datetime) -> bool:
        """Check if task is due to run."""
        if not self._matches_schedule(now):
            return False

        # Check date-aware filters (weekdays, etc.)
        for filter_fn in self._filters:
            if not filter_fn(now):
                return False

        # Check no-arg filters (when, etc.)
        for filter_fn in self._filters_no_arg:
            if not filter_fn():
                return False

        # Check rejects
        for reject_fn in self._rejects:
            if reject_fn():
                return False

        return True

    def _matches_schedule(self, now: datetime) -> bool:
        """Check if current time matches cron expression.

        Note: Converts Python's weekday (0=Monday, 6=Sunday) to cron format (0=Sunday, 6=Saturday)
        """
        parts = self.expression.split()
        if len(parts) != 5:
            return False

        minute, hour, day, month, day_of_week = parts

        if not self._matches_field(minute, now.minute, 0, 59):
            return False
        if not self._matches_field(hour, now.hour, 0, 23):
            return False
        if not self._matches_field(day, now.day, 1, 31):
            return False
        if not self._matches_field(month, now.month, 1, 12):
            return False

        # Convert Python weekday (0=Mon, 6=Sun) to cron weekday (0=Sun, 6=Sat)
        cron_weekday = (now.weekday() + 1) % 7
        if not self._matches_field(day_of_week, cron_weekday, 0, 6):
            return False

        return True

    def _matches_field(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        """Check if a single cron field matches the current value.

        Note: Python's datetime.weekday() returns 0=Monday, 6=Sunday
        but cron uses 0=Sunday, 6=Saturday, so we need to convert.
        """
        if field == "*":
            return True

        # Handle step values (*/5)
        if field.startswith("*/"):
            step = int(field[2:])
            return value % step == 0

        # Handle ranges (1-5)
        if "-" in field:
            start, end = field.split("-")
            return int(start) <= value <= int(end)

        # Handle lists (1,3,5)
        if "," in field:
            return value in [int(x) for x in field.split(",")]

        # Handle single values
        return int(field) == value

    def run(self):
        """Execute the scheduled task."""
        try:
            self.callback()
        except Exception as e:
            print(f"Error running scheduled task '{self.description}': {e}")
            raise

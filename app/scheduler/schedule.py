"""Schedule class for managing scheduled tasks."""

from collections.abc import Callable
from datetime import datetime

from .event import Event


class Schedule:
    """Manages all scheduled tasks."""

    def __init__(self):
        self._events: list[Event] = []

    def call(self, callback: Callable, description: str = "") -> Event:
        """Schedule a callable function."""
        event = Event(callback, description or callback.__name__)
        self._events.append(event)
        return event

    def command(self, command: str, description: str = "") -> Event:
        """Schedule a management command."""

        def run_command():
            import os

            os.system(f"python manage.py {command}")

        event = Event(run_command, description or f"Command: {command}")
        self._events.append(event)
        return event

    def due_events(self, now: datetime | None = None) -> list[Event]:
        """Get all events that are due to run."""
        if now is None:
            now = datetime.now()

        return [event for event in self._events if event.is_due(now)]

    def run_due_tasks(self, now: datetime | None = None):
        """Run all tasks that are due."""
        due = self.due_events(now)

        for event in due:
            print(f"Running: {event.description}")
            try:
                event.run()
                print(f"✓ Completed: {event.description}")
            except Exception as e:
                print(f"✗ Failed: {event.description} - {e}")

    def all_events(self) -> list[Event]:
        """Get all scheduled events."""
        return self._events

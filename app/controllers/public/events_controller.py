from flask import abort, render_template

from app.services import EventService
from app.services.settings_service import SettingsService


class EventsController:
    def __call__(self):
        if not SettingsService.get("events_enabled"):
            abort(404)
        events = EventService.get_upcoming_published_events()
        return render_template("public/events.html", events=events)

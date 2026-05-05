from flask import abort, render_template

from app.services import EventService
from app.services.settings_service import SettingsService


class EventsController:
    def __init__(self):
        super().__init__()
        self.event_service = EventService
        self.settings_service = SettingsService

    def __call__(self):
        if not self.settings_service.get("events_enabled"):
            abort(404)
        events = self.event_service.get_upcoming_published_events()
        return render_template("public/events.html", events=events)

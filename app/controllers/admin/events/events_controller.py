from flask import render_template

from app.services import EventService
from app.utils import permission_required


class EventsController:
    def __init__(self):
        super().__init__()
        self.service = EventService

    @permission_required("events.read")
    def __call__(self):
        events = self.service.get_all_events()
        return render_template("admin/events.html", events=events)

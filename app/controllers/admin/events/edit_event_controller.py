from flask import abort, render_template

from app.forms import EventForm
from app.services import EventService
from app.utils import permission_required


class EditEventController:
    def __init__(self):
        super().__init__()
        self.service = EventService

    @permission_required("events.update")
    def __call__(self, event_id):
        event = self.service.get_event_by_id(event_id)
        if not event:
            abort(404)

        return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))

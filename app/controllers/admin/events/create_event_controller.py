from flask import render_template

from app.forms import EventForm
from app.utils import permission_required


class CreateEventController:
    @permission_required("events.create")
    def __call__(self):
        return render_template("admin/create_event.html", form=EventForm())

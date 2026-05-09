from flask import abort, flash, redirect, render_template, url_for

from app.forms import EventForm
from app.services import EventService
from app.utils import permission_required


class EditEventPostController:
    def __init__(self):
        super().__init__()
        self.service = EventService

    @permission_required("events.update")
    def __call__(self, event_id):
        event = self.service.get_event_by_id(event_id)
        if not event:
            abort(404)

        form = EventForm(obj=event)

        if form.validate_on_submit():
            result = self.service.update_event(
                event=event,
                title=form.title.data,
                start_date=form.start_date.data,
                description=form.description.data,
                location=form.location.data,
                published=form.published.data,
            )

            if not result.success:
                flash(result.message or "An error occurred while updating the event.", "error")
                return render_template("admin/edit_event.html", event=event, form=form)

            flash("Event updated successfully!", "success")
            return redirect(url_for("admin.events"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))

from flask import flash, redirect, render_template, url_for

from app.forms import EventForm
from app.services import EventService
from app.utils import permission_required


class CreateEventPostController:
    def __init__(self):
        super().__init__()
        self.service = EventService

    @permission_required("events.create")
    def __call__(self):
        form = EventForm()

        if form.validate_on_submit():
            result = self.service.create_event(
                title=form.title.data,
                start_date=form.start_date.data,
                description=form.description.data,
                location=form.location.data,
                published=form.published.data,
            )

            if not result.success:
                flash(result.message, "error")
                return render_template("admin/create_event.html", form=form)

            flash("Event created successfully!", "success")
            return redirect(url_for("admin.events"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/create_event.html", form=EventForm())

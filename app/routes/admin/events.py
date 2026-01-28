from flask import abort, flash, redirect, render_template, url_for

from app.forms import EventForm
from app.services import EventService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/events")
@permission_required("events.read")
def events():
    events = EventService.get_all_events()
    return render_template("admin/events.html", events=events)


@bp.get("/events/create")
@permission_required("events.create")
def create_event():
    """Display event creation form"""
    return render_template("admin/create_event.html", form=EventForm())


@bp.post("/events/create")
@permission_required("events.create")
def create_event_post():
    """Handle event creation form submission"""
    form = EventForm()

    if form.validate_on_submit():
        event, error = EventService.create_event(
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_event.html", form=form)

        flash("Event created successfully!", "success")
        return redirect(url_for("admin.events"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_event.html", form=EventForm())


@bp.get("/events/<int:event_id>/edit")
@permission_required("events.update")
def edit_event(event_id):
    """Display event edit form"""
    event = EventService.get_event_by_id(event_id)
    if not event:
        abort(404)

    return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))


@bp.post("/events/<int:event_id>/edit")
@permission_required("events.update")
def edit_event_post(event_id):
    """Handle event edit form submission"""
    event = EventService.get_event_by_id(event_id)
    if not event:
        abort(404)

    form = EventForm(obj=event)

    if form.validate_on_submit():
        success, error = EventService.update_event(
            event=event,
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )

        if not success:
            flash(error or "An error occurred while updating the event.", "error")
            return render_template("admin/edit_event.html", event=event, form=form)

        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))

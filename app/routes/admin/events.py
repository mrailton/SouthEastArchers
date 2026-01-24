from flask import abort, flash, redirect, render_template, url_for

from app.forms import EventForm
from app.services import EventService

from . import admin_required, bp


@bp.get("/events")
@admin_required
def events():
    events = EventService.get_all_events()
    return render_template("admin/events.html", events=events)


@bp.get("/events/create")
@admin_required
def create_event():
    """Display event creation form"""
    return render_template("admin/create_event.html", form=EventForm())


@bp.post("/events/create")
@admin_required
def create_event_post():
    """Handle event creation form submission"""
    form = EventForm()

    if form.validate_on_submit():
        EventService.create_event(
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )

        flash("Event created successfully!", "success")
        return redirect(url_for("admin.events"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_event.html", form=EventForm())


@bp.get("/events/<int:event_id>/edit")
@admin_required
def edit_event(event_id):
    """Display event edit form"""
    event = EventService.get_event_by_id(event_id)
    if not event:
        abort(404)

    return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))


@bp.post("/events/<int:event_id>/edit")
@admin_required
def edit_event_post(event_id):
    """Handle event edit form submission"""
    event = EventService.get_event_by_id(event_id)
    if not event:
        abort(404)

    form = EventForm(obj=event)

    if form.validate_on_submit():
        EventService.update_event(
            event=event,
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )

        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_event.html", event=event, form=EventForm(obj=event))

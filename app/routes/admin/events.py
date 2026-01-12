from flask import abort, flash, redirect, render_template, request, url_for

from app.schemas import EventSchema
from app.services import EventService
from app.utils.pydantic_helpers import validate_request

from . import admin_required, bp


@bp.route("/events")
@admin_required
def events():
    events = EventService.get_all_events()
    return render_template("admin/events.html", events=events)


@bp.route("/events/create", methods=["GET", "POST"])
@admin_required
def create_event():
    if request.method == "POST":
        validated, errors = validate_request(EventSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/create_event.html")

        EventService.create_event(
            title=validated.title,
            start_date=validated.start_date,
            description=validated.description,
            location=validated.location,
            published=validated.published,
        )

        flash("Event created successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/create_event.html")


@bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_event(event_id):
    event = EventService.get_event_by_id(event_id)
    if not event:
        abort(404)

    if request.method == "POST":
        validated, errors = validate_request(EventSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/edit_event.html", event=event)

        EventService.update_event(
            event=event,
            title=validated.title,
            start_date=validated.start_date,
            description=validated.description,
            location=validated.location,
            published=validated.published,
        )

        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/edit_event.html", event=event)

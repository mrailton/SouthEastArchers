from flask import abort, flash, redirect, render_template, request, url_for

from app.services import EventService

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
        start_date = EventService.parse_date(request.form.get("start_date"))
        if not start_date:
            flash("Invalid date format.", "error")
            return render_template("admin/create_event.html")

        EventService.create_event(
            title=request.form.get("title"),
            start_date=start_date,
            description=request.form.get("description"),
            location=request.form.get("location"),
            published=request.form.get("published") == "on",
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
        start_date = EventService.parse_date(request.form.get("start_date"))
        if not start_date:
            flash("Invalid date format.", "error")
            return render_template("admin/edit_event.html", event=event)

        EventService.update_event(
            event=event,
            title=request.form.get("title"),
            start_date=start_date,
            description=request.form.get("description"),
            location=request.form.get("location"),
            published=request.form.get("published") == "on",
        )

        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/edit_event.html", event=event)

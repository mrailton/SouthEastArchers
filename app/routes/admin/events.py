"""Admin event management routes"""

from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from . import bp, admin_required
from app import db
from app.models import Event


@bp.route("/events")
@admin_required
def events():
    """Manage events"""
    events = Event.query.order_by(Event.start_date.desc()).all()
    return render_template("admin/events.html", events=events)


@bp.route("/events/create", methods=["GET", "POST"])
@admin_required
def create_event():
    """Create a new event"""
    if request.method == "POST":
        try:
            start_date_str = request.form.get("start_date")
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            flash("Invalid date format.", "error")
            return render_template("admin/create_event.html")

        event = Event(
            title=request.form.get("title"),
            description=request.form.get("description"),
            start_date=start_date,
            location=request.form.get("location"),
            published=request.form.get("published") == "on",
        )

        db.session.add(event)
        db.session.commit()

        flash("Event created successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/create_event.html")


@bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_event(event_id):
    """Edit an event"""
    event = db.session.get(Event, event_id)
    if not event:
        from flask import abort

        abort(404)

    if request.method == "POST":
        try:
            start_date_str = request.form.get("start_date")
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            flash("Invalid date format.", "error")
            return render_template("admin/edit_event.html", event=event)

        event.title = request.form.get("title")
        event.description = request.form.get("description")
        event.start_date = start_date
        event.location = request.form.get("location")
        event.published = request.form.get("published") == "on"

        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/edit_event.html", event=event)

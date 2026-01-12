from flask import abort, flash, redirect, render_template, request, url_for

from app.schemas import ShootSchema
from app.services import ShootService
from app.utils.pydantic_helpers import validate_request

from . import admin_required, bp


@bp.route("/shoots")
@admin_required
def shoots():
    shoots = ShootService.get_all_shoots()
    return render_template("admin/shoots.html", shoots=shoots)


@bp.route("/shoots/create", methods=["GET", "POST"])
@admin_required
def create_shoot():
    active_members = ShootService.get_active_members_with_credits()

    if request.method == "POST":
        validated, errors = validate_request(ShootSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/create_shoot.html", active_members=active_members)

        shoot, warnings = ShootService.create_shoot(
            shoot_date=validated.date,
            location=validated.location,
            description=validated.description,
            attendee_ids=validated.attendees or [],
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash(f"Shoot created with {len(validated.attendees or [])} attendees!", "success")
        return redirect(url_for("admin.shoots"))

    return render_template("admin/create_shoot.html", active_members=active_members)


@bp.route("/shoots/<int:shoot_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_shoot(shoot_id):
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    active_members = ShootService.get_active_members_with_credits()

    if request.method == "POST":
        validated, errors = validate_request(ShootSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/edit_shoot.html", shoot=shoot, active_members=active_members)

        warnings = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=validated.date,
            location=validated.location,
            description=validated.description,
            attendee_ids=validated.attendees or [],
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash("Shoot updated successfully!", "success")
        return redirect(url_for("admin.shoots"))

    return render_template(
        "admin/edit_shoot.html",
        shoot=shoot,
        active_members=active_members,
    )

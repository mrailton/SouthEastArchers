from flask import abort, flash, redirect, render_template, request, url_for

from app.forms import ShootForm
from app.services import ShootService

from . import admin_required, bp


@bp.route("/shoots")
@admin_required
def shoots():
    shoots = ShootService.get_all_shoots()
    return render_template("admin/shoots.html", shoots=shoots)


@bp.route("/shoots/create", methods=["GET", "POST"])
@admin_required
def create_shoot():
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        shoot, warnings = ShootService.create_shoot(
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash(f"Shoot created with {len(form.attendees.data or [])} attendees!", "success")
        return redirect(url_for("admin.shoots"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    active_members = ShootService.get_active_members_with_credits()
    return render_template("admin/create_shoot.html", active_members=active_members, form=form)


@bp.route("/shoots/<int:shoot_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_shoot(shoot_id):
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if request.method == "GET":
        form.attendees.data = [u.id for u in shoot.users]

    if form.validate_on_submit():
        warnings = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash("Shoot updated successfully!", "success")
        return redirect(url_for("admin.shoots"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    active_members = ShootService.get_active_members_with_credits()
    return render_template(
        "admin/edit_shoot.html",
        shoot=shoot,
        active_members=active_members,
        form=form,
    )

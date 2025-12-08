from flask import abort, flash, redirect, render_template, request, url_for

from app.forms.admin_forms import ShootForm
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
            attendee_ids=form.attendees.data,
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash(f"Shoot created with {len(form.attendees.data)} attendees!", "success")
        return redirect(url_for("admin.shoots"))

    return render_template("admin/create_shoot.html", form=form)


@bp.route("/shoots/<int:shoot_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_shoot(shoot_id):
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        warnings = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data,
        )

        for warning in warnings:
            flash(f"Warning: {warning}", "warning")

        flash("Shoot updated successfully!", "success")
        return redirect(url_for("admin.shoots"))

    if request.method == "GET":
        form.date.data = shoot.date
        form.location.data = shoot.location.name
        form.description.data = shoot.description
        form.attendees.data = [u.id for u in shoot.users]

    return render_template("admin/edit_shoot.html", form=form, shoot=shoot)

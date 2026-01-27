from flask import abort, flash, redirect, render_template, url_for

from app.forms import ShootForm
from app.services import ShootService

from . import admin_required, bp


@bp.get("/shoots")
@admin_required
def shoots():
    shoots = ShootService.get_all_shoots()
    return render_template("admin/shoots.html", shoots=shoots)


@bp.get("/shoots/create")
@admin_required
def create_shoot():
    """Display shoot creation form"""
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()
    active_members = ShootService.get_active_members_with_credits()
    return render_template("admin/create_shoot.html", active_members=active_members, form=form)


@bp.post("/shoots/create")
@admin_required
def create_shoot_post():
    """Handle shoot creation form submission"""
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        shoot, messages = ShootService.create_shoot(
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
        )

        if not shoot:
            for error in messages:
                flash(error, "error")
            active_members = ShootService.get_active_members_with_credits()
            return render_template("admin/create_shoot.html", active_members=active_members, form=form)

        for message in messages:
            flash(f"Warning: {message}", "warning")

        flash(f"Shoot created with {len(form.attendees.data or [])} attendees!", "success")
        return redirect(url_for("admin.shoots"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    active_members = ShootService.get_active_members_with_credits()
    return render_template("admin/create_shoot.html", active_members=active_members, form=form)


@bp.get("/shoots/<int:shoot_id>/edit")
@admin_required
def edit_shoot(shoot_id):
    """Display shoot edit form"""
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()
    form.attendees.data = [u.id for u in shoot.users]

    active_members = ShootService.get_active_members_with_credits()
    return render_template(
        "admin/edit_shoot.html",
        shoot=shoot,
        active_members=active_members,
        form=form,
    )


@bp.post("/shoots/<int:shoot_id>/edit")
@admin_required
def edit_shoot_post(shoot_id):
    """Handle shoot edit form submission"""
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        success, messages = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
        )

        if not success:
            for error in messages:
                flash(error, "error")
            active_members = ShootService.get_active_members_with_credits()
            return render_template(
                "admin/edit_shoot.html",
                shoot=shoot,
                active_members=active_members,
                form=form,
            )

        for message in messages:
            flash(f"Warning: {message}", "warning")

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

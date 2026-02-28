from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.forms import ShootForm
from app.services import ShootService
from app.services.settings_service import SettingsService
from app.utils.decorators import permission_required

from . import bp


def _parse_visitors_from_form() -> list[dict]:
    """Parse visitor data from repeated form fields."""
    visitors = []
    names = request.form.getlist("visitor_name")
    clubs = request.form.getlist("visitor_club")
    affiliations = request.form.getlist("visitor_affiliation")
    payment_methods = request.form.getlist("visitor_payment_method")

    for i in range(len(names)):
        name = names[i].strip() if i < len(names) else ""
        club = clubs[i].strip() if i < len(clubs) else ""
        affiliation = affiliations[i] if i < len(affiliations) else ""
        payment_method = payment_methods[i] if i < len(payment_methods) else ""
        if name and club and affiliation and payment_method:
            visitors.append(
                {
                    "name": name,
                    "club": club,
                    "affiliation": affiliation,
                    "payment_method": payment_method,
                }
            )
    return visitors


@bp.get("/shoots")
@permission_required("shoots.read")
def shoots():
    shoots = ShootService.get_all_shoots()
    return render_template("admin/shoots.html", shoots=shoots)


@bp.get("/shoots/create")
@permission_required("shoots.create")
def create_shoot():
    """Display shoot creation form"""
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()
    active_members = ShootService.get_active_members_with_credits()
    settings = SettingsService.get()
    visitor_fee = settings.visitor_shoot_fee / 100.0
    return render_template("admin/create_shoot.html", active_members=active_members, form=form, visitor_fee=visitor_fee)


@bp.post("/shoots/create")
@permission_required("shoots.create")
def create_shoot_post():
    """Handle shoot creation form submission"""
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        visitors = _parse_visitors_from_form()
        shoot, messages = ShootService.create_shoot(
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
            visitors=visitors,
            created_by_id=current_user.id,
        )

        if not shoot:
            for error in messages:
                flash(error, "error")
            active_members = ShootService.get_active_members_with_credits()
            settings = SettingsService.get()
            visitor_fee = settings.visitor_shoot_fee / 100.0
            return render_template("admin/create_shoot.html", active_members=active_members, form=form, visitor_fee=visitor_fee)

        for message in messages:
            flash(f"Warning: {message}", "warning")

        visitor_count = len(visitors)
        msg = f"Shoot created with {len(form.attendees.data or [])} attendees"
        if visitor_count:
            msg += f" and {visitor_count} visitor{'s' if visitor_count != 1 else ''}"
        flash(f"{msg}!", "success")
        return redirect(url_for("admin.shoots"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    active_members = ShootService.get_active_members_with_credits()
    settings = SettingsService.get()
    visitor_fee = settings.visitor_shoot_fee / 100.0
    return render_template("admin/create_shoot.html", active_members=active_members, form=form, visitor_fee=visitor_fee)


@bp.get("/shoots/<int:shoot_id>/edit")
@permission_required("shoots.update")
def edit_shoot(shoot_id):
    """Display shoot edit form"""
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()
    form.attendees.data = [u.id for u in shoot.users]

    active_members = ShootService.get_active_members_with_credits()
    settings = SettingsService.get()
    visitor_fee = settings.visitor_shoot_fee / 100.0
    return render_template(
        "admin/edit_shoot.html",
        shoot=shoot,
        active_members=active_members,
        form=form,
        visitor_fee=visitor_fee,
    )


@bp.post("/shoots/<int:shoot_id>/edit")
@permission_required("shoots.update")
def edit_shoot_post(shoot_id):
    """Handle shoot edit form submission"""
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        abort(404)

    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()

    if form.validate_on_submit():
        visitors = _parse_visitors_from_form()
        success, messages = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
            visitors=visitors,
            created_by_id=current_user.id,
        )

        if not success:
            for error in messages:
                flash(error, "error")
            active_members = ShootService.get_active_members_with_credits()
            settings = SettingsService.get()
            visitor_fee = settings.visitor_shoot_fee / 100.0
            return render_template(
                "admin/edit_shoot.html",
                shoot=shoot,
                active_members=active_members,
                form=form,
                visitor_fee=visitor_fee,
            )

        for message in messages:
            flash(f"Warning: {message}", "warning")

        flash("Shoot updated successfully!", "success")
        return redirect(url_for("admin.shoots"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    active_members = ShootService.get_active_members_with_credits()
    settings = SettingsService.get()
    visitor_fee = settings.visitor_shoot_fee / 100.0
    return render_template(
        "admin/edit_shoot.html",
        shoot=shoot,
        active_members=active_members,
        form=form,
        visitor_fee=visitor_fee,
    )

"""Admin shoot management routes"""

from flask import flash, redirect, render_template, request, url_for

from app import db
from app.forms.admin_forms import ShootForm
from app.models import Shoot, User

from . import admin_required, bp


@bp.route("/shoots")
@admin_required
def shoots():
    """Manage shoots"""
    shoots = Shoot.query.order_by(Shoot.date.desc()).all()
    return render_template("admin/shoots.html", shoots=shoots)


@bp.route("/shoots/create", methods=["GET", "POST"])
@admin_required
def create_shoot():
    """Create a new shoot and record attendance"""
    form = ShootForm()

    # Populate attendees choices with active members
    active_members = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.attendees.choices = [
        (u.id, f"{u.name} ({u.membership.credits_remaining()} credits)")
        for u in active_members
        if u.membership and u.membership.is_active()
    ]

    if form.validate_on_submit():
        shoot = Shoot(
            date=form.date.data,
            location=form.location.data,
            description=form.description.data,
        )
        db.session.add(shoot)
        db.session.flush()

        # Add attendees and deduct credits
        attendee_ids = form.attendees.data
        for user_id in attendee_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                if user.membership.use_credit():
                    shoot.users.append(user)
                else:
                    flash(f"Warning: {user.name} has no credits remaining.", "warning")

        db.session.commit()
        flash(f"Shoot created with {len(attendee_ids)} attendees!", "success")
        return redirect(url_for("admin.shoots"))

    return render_template("admin/create_shoot.html", form=form)


@bp.route("/shoots/<int:shoot_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_shoot(shoot_id):
    """Edit an existing shoot"""
    shoot = db.session.get(Shoot, shoot_id)
    if not shoot:
        from flask import abort

        abort(404)

    form = ShootForm()

    # Populate attendees choices with active members
    active_members = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.attendees.choices = [
        (u.id, f"{u.name} ({u.membership.credits_remaining()} credits)")
        for u in active_members
        if u.membership and u.membership.is_active()
    ]

    if form.validate_on_submit():
        # Track credit changes
        old_attendee_ids = {u.id for u in shoot.users}
        new_attendee_ids = set(form.attendees.data)

        # Users removed - refund credits
        removed_ids = old_attendee_ids - new_attendee_ids
        for user_id in removed_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                user.membership.add_credits(1)

        # Users added - deduct credits
        added_ids = new_attendee_ids - old_attendee_ids
        for user_id in added_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                if user.membership.use_credit():
                    shoot.users.append(user)
                else:
                    flash(f"Warning: {user.name} has no credits remaining.", "warning")

        # Remove old attendees
        shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]

        # Update shoot details
        shoot.date = form.date.data
        shoot.location = form.location.data
        shoot.description = form.description.data

        db.session.commit()
        flash("Shoot updated successfully!", "success")
        return redirect(url_for("admin.shoots"))

    # Pre-populate form
    if request.method == "GET":
        form.date.data = shoot.date
        form.location.data = shoot.location.name
        form.description.data = shoot.description
        form.attendees.data = [u.id for u in shoot.users]

    return render_template("admin/edit_shoot.html", form=form, shoot=shoot)

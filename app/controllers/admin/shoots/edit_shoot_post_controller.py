from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user

from app.forms import ShootForm
from app.services import ShootService
from app.services.settings_service import SettingsService
from app.utils import parse_visitors_from_form, permission_required


class EditShootPostController:
    @permission_required("shoots.update")
    def __call__(self, shoot_id):
        shoot = ShootService.get_shoot_by_id(shoot_id)
        if not shoot:
            abort(404)

        form = ShootForm(obj=shoot)
        form.attendees.choices = ShootService.get_active_members_with_credits()

        if form.validate_on_submit():
            visitors = parse_visitors_from_form()
            result = ShootService.update_shoot(
                shoot=shoot,
                shoot_date=form.date.data,
                location=form.location.data,
                description=form.description.data,
                attendee_ids=form.attendees.data or [],
                visitors=visitors,
                created_by_id=current_user.id,
            )

            if not result.success:
                flash(result.message, "error")
                active_members = ShootService.get_active_members_with_credits()
                visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
                return render_template(
                    "admin/edit_shoot.html",
                    shoot=shoot,
                    active_members=active_members,
                    form=form,
                    visitor_fee=visitor_fee,
                )

            for message in result.warnings:
                flash(f"Warning: {message}", "warning")

            flash("Shoot updated successfully!", "success")
            return redirect(url_for("admin.shoots"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        active_members = ShootService.get_active_members_with_credits()
        visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
        return render_template(
            "admin/edit_shoot.html",
            shoot=shoot,
            active_members=active_members,
            form=form,
            visitor_fee=visitor_fee,
        )

"""Admin routes for application settings management."""

from flask import flash, redirect, render_template, url_for

from app import db
from app.forms.admin_forms import SettingsForm
from app.services.settings_service import SettingsService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/settings")
@permission_required("settings.read")
def settings():
    """Display application settings."""
    settings_obj = SettingsService.get()

    form = SettingsForm()
    # Populate form with current values
    form.membership_year_start_month.data = settings_obj.membership_year_start_month
    form.membership_year_start_day.data = settings_obj.membership_year_start_day
    form.annual_membership_cost.data = settings_obj.annual_membership_cost // 100  # Convert cents to euros
    form.membership_shoots_included.data = settings_obj.membership_shoots_included
    form.additional_shoot_cost.data = settings_obj.additional_shoot_cost // 100  # Convert cents to euros

    return render_template("admin/settings.html", form=form)


@bp.post("/settings")
@permission_required("settings.write")
def settings_post():
    """Update application settings."""
    form = SettingsForm()

    if form.validate_on_submit():
        try:
            settings_obj = SettingsService.get()

            # Update all settings (convert euros to cents for costs)
            settings_obj.membership_year_start_month = form.membership_year_start_month.data
            settings_obj.membership_year_start_day = form.membership_year_start_day.data
            settings_obj.annual_membership_cost = form.annual_membership_cost.data * 100  # Convert to cents
            settings_obj.membership_shoots_included = form.membership_shoots_included.data
            settings_obj.additional_shoot_cost = form.additional_shoot_cost.data * 100  # Convert to cents

            SettingsService.save(settings_obj)

            flash("Settings updated successfully!", "success")
            return redirect(url_for("admin.settings"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}", "error")

    # If validation fails, show errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")

    return render_template("admin/settings.html", form=form)

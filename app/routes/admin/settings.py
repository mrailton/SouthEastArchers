"""Admin routes for application settings management."""

from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import SettingsForm
from app.services.settings_service import SettingsService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/settings")
@permission_required("settings.read")
def settings():
    """Display application settings."""
    all_settings = SettingsService.get_all()

    form = SettingsForm()
    # Populate form with current values
    form.membership_year_start_month.data = all_settings["membership_year_start_month"]
    form.membership_year_start_day.data = all_settings["membership_year_start_day"]
    form.annual_membership_cost.data = all_settings["annual_membership_cost"] // 100  # Convert cents to euros
    form.membership_shoots_included.data = all_settings["membership_shoots_included"]
    form.additional_shoot_cost.data = all_settings["additional_shoot_cost"] // 100  # Convert cents to euros
    form.visitor_shoot_fee.data = all_settings["visitor_shoot_fee"] // 100  # Convert cents to euros
    form.cash_payment_instructions.data = all_settings["cash_payment_instructions"]
    form.sumup_fee_percentage.data = all_settings["sumup_fee_percentage"]
    form.news_enabled.data = all_settings["news_enabled"]
    form.events_enabled.data = all_settings["events_enabled"]

    return render_template("admin/settings.html", form=form)


@bp.post("/settings")
@permission_required("settings.write")
def settings_post():
    """Update application settings."""
    form = SettingsForm()

    if form.validate_on_submit():
        try:
            SettingsService.save_many(
                {
                    "membership_year_start_month": form.membership_year_start_month.data,
                    "membership_year_start_day": form.membership_year_start_day.data,
                    "annual_membership_cost": form.annual_membership_cost.data * 100,  # Convert to cents
                    "membership_shoots_included": form.membership_shoots_included.data,
                    "additional_shoot_cost": form.additional_shoot_cost.data * 100,  # Convert to cents
                    "visitor_shoot_fee": form.visitor_shoot_fee.data * 100,  # Convert to cents
                    "cash_payment_instructions": form.cash_payment_instructions.data,
                    "sumup_fee_percentage": form.sumup_fee_percentage.data,
                    "news_enabled": form.news_enabled.data,
                    "events_enabled": form.events_enabled.data,
                }
            )

            flash("Settings updated successfully!", "success")
            return redirect(url_for("admin.settings"))
        except Exception as e:
            flash(f"Error updating settings: {str(e)}", "error")

    # If validation fails, show errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")

    return render_template("admin/settings.html", form=form)

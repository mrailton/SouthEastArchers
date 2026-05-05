from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import SettingsForm
from app.services.settings_service import SettingsService
from app.utils import permission_required


class SettingsPostController:
    def __init__(self):
        super().__init__()
        self.service = SettingsService

    @permission_required("settings.write")
    def __call__(self):
        form = SettingsForm()

        if form.validate_on_submit():
            try:
                self.service.save_many(
                    {
                        "membership_year_start_month": form.membership_year_start_month.data,
                        "membership_year_start_day": form.membership_year_start_day.data,
                        "annual_membership_cost": form.annual_membership_cost.data * 100,
                        "membership_shoots_included": form.membership_shoots_included.data,
                        "additional_shoot_cost": form.additional_shoot_cost.data * 100,
                        "visitor_shoot_fee": form.visitor_shoot_fee.data * 100,
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

        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

        return render_template("admin/settings.html", form=form)

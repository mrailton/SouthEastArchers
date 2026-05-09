from flask import render_template

from app.forms.admin_forms import SettingsForm
from app.services.settings_service import SettingsService
from app.utils import permission_required


class SettingsController:
    def __init__(self):
        super().__init__()
        self.service = SettingsService

    @permission_required("settings.read")
    def __call__(self):
        all_settings = self.service.get_all()

        form = SettingsForm()
        form.membership_year_start_month.data = all_settings["membership_year_start_month"]
        form.membership_year_start_day.data = all_settings["membership_year_start_day"]
        form.annual_membership_cost.data = all_settings["annual_membership_cost"] // 100
        form.membership_shoots_included.data = all_settings["membership_shoots_included"]
        form.additional_shoot_cost.data = all_settings["additional_shoot_cost"] // 100
        form.visitor_shoot_fee.data = all_settings["visitor_shoot_fee"] // 100
        form.cash_payment_instructions.data = all_settings["cash_payment_instructions"]
        form.sumup_fee_percentage.data = all_settings["sumup_fee_percentage"]
        form.news_enabled.data = all_settings["news_enabled"]
        form.events_enabled.data = all_settings["events_enabled"]

        return render_template("admin/settings.html", form=form)

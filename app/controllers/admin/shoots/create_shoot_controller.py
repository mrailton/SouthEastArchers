from flask import render_template

from app.forms import ShootForm
from app.services import ShootService
from app.services.settings_service import SettingsService
from app.utils import permission_required


class CreateShootController:
    @permission_required("shoots.create")
    def __call__(self):
        form = ShootForm()
        form.attendees.choices = ShootService.get_active_members_with_credits()
        active_members = ShootService.get_active_members_with_credits()
        visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
        return render_template("admin/create_shoot.html", active_members=active_members, form=form, visitor_fee=visitor_fee)

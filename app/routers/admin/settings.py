from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, verify_csrf
from app.forms.admin_forms import SettingsForm
from app.utils.formdata import request_form_data
from app.routers.admin._helpers import flash_form_errors, require_perms
from app.services.settings_service import SettingsService
from app.templating import flash, render

router = APIRouter(tags=["admin.settings"])


def _populate_settings_form(form: SettingsForm, all_settings: dict) -> None:
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


@router.get("/settings", name="admin.settings", dependencies=[require_perms("settings.read")])
async def settings_page(request: Request, db: DbSession, user: CurrentUser):
    all_settings = SettingsService.get_all()
    form = SettingsForm()
    _populate_settings_form(form, all_settings)
    return render(request, "admin/settings.html", {"form": form}, user=user, db=db)


@router.post("/settings", name="admin.settings_post", dependencies=[require_perms("settings.write")])
async def settings_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = SettingsForm(formdata=form_data)
    if form.validate():
        try:
            SettingsService.save_many(
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
            flash(request, "success", "Settings updated successfully!")
            return RedirectResponse(url="/admin/settings", status_code=303)
        except Exception as exc:
            flash(request, "error", f"Error updating settings: {exc}")
    flash_form_errors(request, form)
    return render(request, "admin/settings.html", {"form": form}, user=user, db=db, status_code=422)

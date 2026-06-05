from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import SETTINGS_FIELD_DESCRIPTIONS, SettingsForm
from app.schemas.form_helpers import FormView, parse_form
from app.services import settings
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.settings"])

_SETTINGS_FIELD_TYPES = {
    "membership_year_start_month": "number",
    "membership_year_start_day": "number",
    "annual_membership_cost": "number",
    "membership_shoots_included": "number",
    "additional_shoot_cost": "number",
    "visitor_shoot_fee": "number",
    "cash_payment_instructions": "textarea",
    "sumup_fee_percentage": "number",
    "news_enabled": "checkbox",
    "events_enabled": "checkbox",
}


def _settings_form_view(values: dict, *, errors: dict | None = None) -> FormView:
    return FormView(
        values=values,
        errors=errors,
        descriptions=SETTINGS_FIELD_DESCRIPTIONS,
        field_types=_SETTINGS_FIELD_TYPES,
    )


def _settings_values_from_store(all_settings: dict) -> dict:
    return {
        "membership_year_start_month": all_settings["membership_year_start_month"],
        "membership_year_start_day": all_settings["membership_year_start_day"],
        "annual_membership_cost": all_settings["annual_membership_cost"] // 100,
        "membership_shoots_included": all_settings["membership_shoots_included"],
        "additional_shoot_cost": all_settings["additional_shoot_cost"] // 100,
        "visitor_shoot_fee": all_settings["visitor_shoot_fee"] // 100,
        "cash_payment_instructions": all_settings["cash_payment_instructions"],
        "sumup_fee_percentage": all_settings["sumup_fee_percentage"],
        "news_enabled": all_settings["news_enabled"],
        "events_enabled": all_settings["events_enabled"],
    }


@router.get("/settings", name="admin.settings", dependencies=[require_perms("settings.read")])
async def settings_page(request: Request, db: DbSession, user: CurrentUser):
    form = _settings_form_view(_settings_values_from_store(settings.get_all()))
    return render(request, "admin/settings.html", {"form": form}, user=user)


@router.post("/settings", name="admin.settings_post", dependencies=[require_perms("settings.write")])
async def settings_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    parsed, errors, values = parse_form(SettingsForm, form_data)
    if parsed:
        try:
            settings.save_many(
                {
                    "membership_year_start_month": parsed.membership_year_start_month,
                    "membership_year_start_day": parsed.membership_year_start_day,
                    "annual_membership_cost": parsed.annual_membership_cost * 100,
                    "membership_shoots_included": parsed.membership_shoots_included,
                    "additional_shoot_cost": parsed.additional_shoot_cost * 100,
                    "visitor_shoot_fee": parsed.visitor_shoot_fee * 100,
                    "cash_payment_instructions": parsed.cash_payment_instructions,
                    "sumup_fee_percentage": parsed.sumup_fee_percentage,
                    "news_enabled": parsed.news_enabled,
                    "events_enabled": parsed.events_enabled,
                }
            )
            flash(request, "success", "Settings updated successfully!")
            return RedirectResponse(url="/admin/settings", status_code=303)
        except Exception as exc:
            flash(request, "error", f"Error updating settings: {exc}")
    flash_form_errors(request, errors)
    form = _settings_form_view(values, errors=errors)
    return render(request, "admin/settings.html", {"form": form}, user=user, status_code=422)

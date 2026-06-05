from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CsrfFormData, CurrentUser, require_perms
from app.routes.admin._helpers import flash_form_errors, flash_service_warnings
from app.schemas.admin_forms import ShootForm
from app.schemas.form_helpers import parse_form
from app.services import settings, shoots
from app.templating import flash, render
from app.utils.formdata import parse_visitors_from_form

router = APIRouter(tags=["admin.shoots"])


def _shoot_page_context():
    active_members = shoots.get_active_members_with_credits()
    visitor_fee = settings.get("visitor_shoot_fee") / 100.0
    return {"active_members": active_members, "visitor_fee": visitor_fee}


@router.get("/shoots", name="admin.shoots", dependencies=[require_perms("shoots.read")])
def shoots_index(request: Request, user: CurrentUser):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 10))
    if per_page not in (5, 10, 20, 50, 100):
        per_page = 10
    pagination = shoots.get_all_shoots_paginated(page=page, per_page=per_page)
    return render(
        request,
        "admin/shoots.html",
        {"shoots": pagination.items, "pagination": pagination, "per_page": per_page},
        user=user,
    )


@router.get("/shoots/create", name="admin.create_shoot", dependencies=[require_perms("shoots.create")])
def create_shoot_page(request: Request, user: CurrentUser):
    return render(request, "admin/create_shoot.html", _shoot_page_context(), user=user)


@router.post("/shoots/create", name="admin.create_shoot_post", dependencies=[require_perms("shoots.create")])
def create_shoot_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, _values = parse_form(ShootForm, form_data)
    if parsed:
        visitors = parse_visitors_from_form(form_data)
        result = shoots.create_shoot(
            shoot_date=parsed.date,
            location=parsed.location,
            description=parsed.description,
            attendee_ids=parsed.attendees,
            visitors=visitors,
            created_by_id=user.id,
        )
        if result.success:
            flash_service_warnings(request, result)
            visitor_count = len(visitors)
            msg = f"Shoot created with {len(parsed.attendees)} attendees"
            if visitor_count:
                msg += f" and {visitor_count} visitor{'s' if visitor_count != 1 else ''}"
            flash(request, "success", f"{msg}!")
            return RedirectResponse(url="/admin/shoots", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    return render(request, "admin/create_shoot.html", _shoot_page_context(), user=user, status_code=422)


@router.get("/shoots/{shoot_id}/edit", name="admin.edit_shoot", dependencies=[require_perms("shoots.update")])
def edit_shoot_page(shoot_id: int, request: Request, user: CurrentUser):
    shoot = shoots.get_shoot_by_id(shoot_id)
    if not shoot:
        return render(request, "errors/404.html", user=user, status_code=404)
    context = _shoot_page_context()
    context["shoot"] = shoot
    return render(request, "admin/edit_shoot.html", context, user=user)


@router.post("/shoots/{shoot_id}/edit", name="admin.edit_shoot_post", dependencies=[require_perms("shoots.update")])
def edit_shoot_store(shoot_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    shoot = shoots.get_shoot_by_id(shoot_id)
    if not shoot:
        return render(request, "errors/404.html", user=user, status_code=404)
    parsed, errors, _values = parse_form(ShootForm, form_data)
    if parsed:
        visitors = parse_visitors_from_form(form_data)
        result = shoots.update_shoot(
            shoot,
            shoot_date=parsed.date,
            location=parsed.location,
            description=parsed.description,
            attendee_ids=parsed.attendees,
            visitors=visitors,
            created_by_id=user.id,
        )
        if result.success:
            flash_service_warnings(request, result)
            flash(request, "success", "Shoot updated!")
            return RedirectResponse(url="/admin/shoots", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    context = _shoot_page_context()
    context["shoot"] = shoot
    return render(request, "admin/edit_shoot.html", context, user=user, status_code=422)

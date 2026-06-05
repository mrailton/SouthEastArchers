from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.forms.admin_forms import ShootForm
from app.routes.admin._helpers import flash_form_errors, flash_service_warnings
from app.services.settings_service import SettingsService
from app.services.shoot_service import ShootService
from app.templating import flash, render
from app.utils.formdata import parse_visitors_from_form, request_form_data

router = APIRouter(tags=["admin.shoots"])


@router.get("/shoots", name="admin.shoots", dependencies=[require_perms("shoots.read")])
async def shoots_index(request: Request, db: DbSession, user: CurrentUser):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 10))
    if per_page not in (5, 10, 20, 50, 100):
        per_page = 10
    pagination = ShootService.get_all_shoots_paginated(page=page, per_page=per_page)
    return render(
        request,
        "admin/shoots.html",
        {"shoots": pagination.items, "pagination": pagination, "per_page": per_page},
        user=user,
        db=db,
    )


@router.get("/shoots/create", name="admin.create_shoot", dependencies=[require_perms("shoots.create")])
async def create_shoot_page(request: Request, db: DbSession, user: CurrentUser):
    form = ShootForm()
    form.attendees.choices = ShootService.get_active_members_with_credits()
    active_members = ShootService.get_active_members_with_credits()
    visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
    return render(
        request,
        "admin/create_shoot.html",
        {"form": form, "active_members": active_members, "visitor_fee": visitor_fee},
        user=user,
        db=db,
    )


@router.post("/shoots/create", name="admin.create_shoot_post", dependencies=[require_perms("shoots.create")])
async def create_shoot_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = ShootForm(formdata=form_data)
    form.attendees.choices = ShootService.get_active_members_with_credits()
    if form.validate():
        visitors = parse_visitors_from_form(form_data)
        result = ShootService.create_shoot(
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
            visitors=visitors,
            created_by_id=user.id,
        )
        if result.success:
            flash_service_warnings(request, result)
            visitor_count = len(visitors)
            msg = f"Shoot created with {len(form.attendees.data or [])} attendees"
            if visitor_count:
                msg += f" and {visitor_count} visitor{'s' if visitor_count != 1 else ''}"
            flash(request, "success", f"{msg}!")
            return RedirectResponse(url="/admin/shoots", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    active_members = ShootService.get_active_members_with_credits()
    visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
    return render(
        request,
        "admin/create_shoot.html",
        {"form": form, "active_members": active_members, "visitor_fee": visitor_fee},
        user=user,
        db=db,
        status_code=422,
    )


@router.get("/shoots/{shoot_id}/edit", name="admin.edit_shoot", dependencies=[require_perms("shoots.update")])
async def edit_shoot_page(shoot_id: int, request: Request, db: DbSession, user: CurrentUser):
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = ShootForm(obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()
    form.attendees.data = [u.id for u in shoot.users]
    active_members = ShootService.get_active_members_with_credits()
    visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
    return render(
        request,
        "admin/edit_shoot.html",
        {"form": form, "shoot": shoot, "active_members": active_members, "visitor_fee": visitor_fee},
        user=user,
        db=db,
    )


@router.post("/shoots/{shoot_id}/edit", name="admin.edit_shoot_post", dependencies=[require_perms("shoots.update")])
async def edit_shoot_store(shoot_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    shoot = ShootService.get_shoot_by_id(shoot_id)
    if not shoot:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = ShootForm(formdata=form_data, obj=shoot)
    form.attendees.choices = ShootService.get_active_members_with_credits()
    if form.validate():
        visitors = parse_visitors_from_form(form_data)
        result = ShootService.update_shoot(
            shoot,
            shoot_date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            attendee_ids=form.attendees.data or [],
            visitors=visitors,
            created_by_id=user.id,
        )
        if result.success:
            flash_service_warnings(request, result)
            flash(request, "success", "Shoot updated!")
            return RedirectResponse(url="/admin/shoots", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    active_members = ShootService.get_active_members_with_credits()
    visitor_fee = SettingsService.get("visitor_shoot_fee") / 100.0
    return render(
        request,
        "admin/edit_shoot.html",
        {"form": form, "shoot": shoot, "active_members": active_members, "visitor_fee": visitor_fee},
        user=user,
        db=db,
        status_code=422,
    )

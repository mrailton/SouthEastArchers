from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, verify_csrf
from app.schemas.form_helpers import parse_form, single_field_errors
from app.schemas.forms import ChangePasswordForm, ProfileForm
from app.services import credits, users
from app.templating import flash, flash_field_errors, render
from app.utils.formdata import request_form_data

router = APIRouter(prefix="/member", tags=["member"])


@router.get("/dashboard", name="member.dashboard")
async def dashboard(
    request: Request,
    user: CurrentUser,
    page: int = Query(1, ge=1),
):
    payment_page = users.get_user_payments_paginated(user.id, page=page, per_page=5)
    return render(
        request,
        "member/dashboard.html",
        {
            "membership": user.membership,
            "shoots_attended": len(user.shoots),
            "payments": payment_page,
        },
        user=user,
    )


@router.get("/shoots", name="member.shoots")
async def shoots(request: Request, user: CurrentUser):
    user_shoots = users.get_user_shoots(user)
    return render(request, "member/shoots.html", {"shoots": user_shoots}, user=user)


@router.get("/credits", name="member.credits")
async def credits_page(request: Request, user: CurrentUser):
    user_credits = credits.get_user_credits(user.id)
    return render(request, "member/credits.html", {"credits": user_credits}, user=user)


@router.get("/profile", name="member.profile")
async def profile(request: Request, user: CurrentUser):
    return render(request, "member/profile.html", user=user)


@router.post("/profile", name="member.profile_post")
async def profile_update(request: Request, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form, errors, _values = parse_form(ProfileForm, form_data)
    if errors:
        return render(
            request,
            "member/profile.html",
            {"errors": single_field_errors(errors)},
            user=user,
            status_code=422,
        )

    assert form is not None
    result = users.update_profile(user, name=form.name, phone=form.phone or None)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url="/member/profile", status_code=303)


@router.get("/change-password", name="member.change_password")
async def change_password_page(request: Request, user: CurrentUser):
    return render(request, "member/change_password.html", user=user)


@router.post("/change-password", name="member.change_password_post")
async def change_password_store(request: Request, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form, errors, _values = parse_form(ChangePasswordForm, form_data)
    if errors:
        flash_field_errors(request, errors)
        return render(
            request,
            "member/change_password.html",
            {"errors": single_field_errors(errors)},
            user=user,
            status_code=422,
        )

    assert form is not None
    result = users.change_password(
        user,
        current_password=form.current_password,
        new_password=form.new_password,
    )
    if not result.success:
        flash(request, "error", result.message)
        return render(request, "member/change_password.html", user=user, status_code=422)

    flash(request, "success", result.message)
    return RedirectResponse(url="/member/profile", status_code=303)

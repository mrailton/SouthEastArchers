from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.core.database import mark_for_commit
from app.dependencies import CurrentUser, DbSession, verify_csrf
from app.schemas.forms import ChangePasswordForm, ProfileForm
from app.services import credits as credit_service
from app.services import users as user_service
from app.templating import flash, render

router = APIRouter(prefix="/member", tags=["member"])


def _validation_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        errors[field or "form"] = error["msg"]
    return errors


@router.get("/dashboard", name="member.dashboard")
async def dashboard(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
):
    payments = user_service.get_user_payments_paginated(db, user.id, page=page, per_page=5)
    return render(
        request,
        "member/dashboard.html",
        {
            "membership": user.membership,
            "shoots_attended": len(user.shoots),
            "payments": payments,
        },
        user=user,
        db=db,
    )


@router.get("/shoots", name="member.shoots")
async def shoots(request: Request, db: DbSession, user: CurrentUser):
    user_shoots = sorted(user.shoots, key=lambda shoot: shoot.date, reverse=True)
    return render(request, "member/shoots.html", {"shoots": user_shoots}, user=user, db=db)


@router.get("/credits", name="member.credits")
async def credits(request: Request, db: DbSession, user: CurrentUser):
    user_credits = credit_service.get_user_credits(db, user.id)
    return render(request, "member/credits.html", {"credits": user_credits}, user=user, db=db)


@router.get("/profile", name="member.profile")
async def profile(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "member/profile.html", user=user, db=db)


@router.post("/profile", name="member.profile_post")
async def profile_update(request: Request, db: DbSession, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        form = ProfileForm(
            csrf_token=str(raw.get("csrf_token", "")),
            name=str(raw.get("name", "")),
            phone=str(raw.get("phone", "")),
        )
    except ValidationError as exc:
        return render(
            request,
            "member/profile.html",
            {"errors": _validation_errors(exc)},
            user=user,
            db=db,
            status_code=422,
        )

    result = user_service.update_profile(user, name=form.name, phone=form.phone or None, db=db)
    mark_for_commit(db)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url="/member/profile", status_code=303)


@router.get("/change-password", name="member.change_password")
async def change_password_page(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "member/change_password.html", user=user, db=db)


@router.post("/change-password", name="member.change_password_post")
async def change_password_store(request: Request, db: DbSession, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        form = ChangePasswordForm(
            csrf_token=str(raw.get("csrf_token", "")),
            current_password=str(raw.get("current_password", "")),
            new_password=str(raw.get("new_password", "")),
            confirm_password=str(raw.get("confirm_password", "")),
        )
    except ValidationError as exc:
        for message in _validation_errors(exc).values():
            flash(request, "error", message)
        return render(
            request,
            "member/change_password.html",
            {"errors": _validation_errors(exc)},
            user=user,
            db=db,
            status_code=422,
        )

    result = user_service.change_password(
        user,
        current_password=form.current_password,
        new_password=form.new_password,
        db=db,
    )
    if not result.success:
        flash(request, "error", result.message)
        return render(request, "member/change_password.html", user=user, db=db, status_code=422)

    mark_for_commit(db)
    flash(request, "success", result.message)
    return RedirectResponse(url="/member/profile", status_code=303)

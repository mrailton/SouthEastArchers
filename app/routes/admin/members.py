from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CsrfFormData, CurrentUser, require_perms
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import QUALIFICATION_CHOICES, CreateMemberForm, EditMemberForm
from app.schemas.form_helpers import FormView, parse_form
from app.services import memberships, rbac, users
from app.templating import flash, render

router = APIRouter(tags=["admin.members"])


def _role_choices():
    return rbac.role_choices()


def _member_form_view(member, *, errors: dict | None = None) -> FormView:
    values = {
        "name": member.name,
        "email": member.email,
        "phone": member.phone or "",
        "qualification": member.qualification or "none",
        "qualification_detail": member.qualification_detail or "",
        "password": "",
        "roles": [role.id for role in member.roles],
        "is_active": member.is_active,
        "membership_start_date": member.membership.start_date if member.membership else None,
        "membership_expiry_date": member.membership.expiry_date if member.membership else None,
        "membership_initial_credits": member.membership.initial_credits if member.membership else None,
        "membership_purchased_credits": member.membership.purchased_credits if member.membership else None,
    }
    return FormView(
        values=values,
        errors=errors,
        choices={"roles": _role_choices(), "qualification": QUALIFICATION_CHOICES},
    )


@router.get("/members", name="admin.members", dependencies=[require_perms("members.read")])
def members_index(request: Request, user: CurrentUser):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 20))
    if per_page not in (5, 10, 20, 50, 100):
        per_page = 10
    search = request.query_params.get("search", "").strip()
    membership_filter = request.query_params.get("membership", "all")
    if membership_filter not in ("all", "with", "without"):
        membership_filter = "all"
    pagination = users.get_all_users_paginated(page=page, per_page=per_page, search=search, membership_filter=membership_filter)
    return render(
        request,
        "admin/members.html",
        {
            "members": pagination.items,
            "pagination": pagination,
            "per_page": per_page,
            "search": search,
            "membership_filter": membership_filter,
        },
        user=user,
    )


@router.get("/members/create", name="admin.create_member", dependencies=[require_perms("members.create")])
def create_member_page(request: Request, user: CurrentUser):
    form = FormView(choices={"roles": _role_choices()})
    return render(request, "admin/create_member.html", {"form": form}, user=user)


@router.post("/members/create", name="admin.create_member_post", dependencies=[require_perms("members.create")])
def create_member_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, values = parse_form(CreateMemberForm, form_data)
    form = FormView(values=values, errors=errors, choices={"roles": _role_choices()})
    if parsed:
        result = users.create_member(
            name=parsed.name,
            email=str(parsed.email),
            phone=parsed.phone or None,
            password=parsed.password or "changeme123",
            role_ids=parsed.roles,
            create_membership=parsed.create_membership,
        )
        if result.success:
            flash(request, "success", f"Member {parsed.name} created successfully!")
            member_id = result.data.id if result.data else None
            if member_id:
                return RedirectResponse(url=f"/admin/members/{member_id}", status_code=303)
            return RedirectResponse(url="/admin/members", status_code=303)
        flash(request, "error", result.message)
        return render(request, "admin/create_member.html", {"form": form}, user=user)
    flash_form_errors(request, errors)
    return render(request, "admin/create_member.html", {"form": form}, user=user, status_code=422)


@router.get("/members/{user_id}", name="admin.member_detail", dependencies=[require_perms("members.read")])
def member_detail(user_id: int, request: Request, user: CurrentUser):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    return render(request, "admin/member_detail.html", {"member": member}, user=user)


@router.get("/members/{user_id}/edit", name="admin.edit_member", dependencies=[require_perms("members.update")])
def edit_member_page(user_id: int, request: Request, user: CurrentUser):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    return render(request, "admin/edit_member.html", {"member": member, "form": _member_form_view(member)}, user=user)


@router.post("/members/{user_id}/edit", name="admin.edit_member_post", dependencies=[require_perms("members.update")])
def edit_member_store(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    parsed, errors, values = parse_form(EditMemberForm, form_data)
    form = FormView(values=values, errors=errors, choices={"roles": _role_choices(), "qualification": QUALIFICATION_CHOICES})
    if parsed:
        result = users.update_member(
            user=member,
            name=parsed.name,
            email=str(parsed.email),
            phone=parsed.phone or None,
            qualification=parsed.qualification,
            qualification_detail=parsed.qualification_detail or None,
            role_ids=parsed.roles,
            is_active=parsed.is_active,
            password=parsed.password or None,
            membership_start_date=parsed.membership_start_date,
            membership_expiry_date=parsed.membership_expiry_date,
            membership_initial_credits=parsed.membership_initial_credits,
            membership_purchased_credits=parsed.membership_purchased_credits,
        )
        flash(request, "success" if result.success else "error", result.message)
        if result.success:
            return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    flash_form_errors(request, errors)
    return render(request, "admin/edit_member.html", {"member": member, "form": form}, user=user, status_code=422)


@router.post("/members/{user_id}/activate", name="admin.activate_user", dependencies=[require_perms("members.activate_account")])
def activate_user(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    result = users.activate_account(user_id)
    flash(request, "success" if result.success else ("warning" if "already active" in result.message else "error"), result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/renew",
    name="admin.renew_membership",
    dependencies=[require_perms("members.manage_membership")],
)
def renew_membership(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    result = memberships.renew_membership(member)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/create",
    name="admin.create_membership",
    dependencies=[require_perms("members.manage_membership")],
)
def create_membership(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    result = memberships.create_membership(member)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/activate",
    name="admin.activate_membership",
    dependencies=[require_perms("members.manage_membership")],
)
def activate_membership(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    result = memberships.activate_membership_for_admin(member)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/credits/adjust",
    name="admin.adjust_credits",
    dependencies=[require_perms("members.manage_membership")],
)
def adjust_credits(user_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    member = users.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, status_code=404)
    if not member.membership:
        flash(request, "error", "Member does not have a membership.")
        return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    try:
        quantity = int(form_data.get("quantity") or "0")
        action = form_data.get("action") or "add"
    except ValueError:
        flash(request, "error", "Please enter a valid number of credits.")
        return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    reason = (form_data.get("reason") or "").strip() or "Admin adjustment"
    result = users.adjust_member_credits(
        member,
        admin_user_id=user.id,
        quantity=quantity,
        action=action,
        reason=reason,
    )
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)

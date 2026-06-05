from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.events import membership_activated
from app.forms.admin_forms import CreateMemberForm, EditMemberForm
from app.routes.admin._helpers import flash_form_errors
from app.services.membership_service import MembershipService
from app.services.payment_service import PaymentService
from app.services.rbac_service import RBACService
from app.services.user_service import UserService
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.members"])


def _role_choices():
    return RBACService.role_choices()


@router.get("/members", name="admin.members", dependencies=[require_perms("members.read")])
async def members_index(request: Request, db: DbSession, user: CurrentUser):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 20))
    if per_page not in (5, 10, 20, 50, 100):
        per_page = 10
    search = request.query_params.get("search", "").strip()
    membership_filter = request.query_params.get("membership", "all")
    if membership_filter not in ("all", "with", "without"):
        membership_filter = "all"
    pagination = UserService.get_all_users_paginated(page=page, per_page=per_page, search=search, membership_filter=membership_filter)
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
        db=db,
    )


@router.get("/members/create", name="admin.create_member", dependencies=[require_perms("members.create")])
async def create_member_page(request: Request, db: DbSession, user: CurrentUser):
    form = CreateMemberForm()
    form.roles.choices = _role_choices()
    return render(request, "admin/create_member.html", {"form": form}, user=user, db=db)


@router.post("/members/create", name="admin.create_member_post", dependencies=[require_perms("members.create")])
async def create_member_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = CreateMemberForm(formdata=form_data)
    form.roles.choices = _role_choices()
    if form.validate():
        result = UserService.create_member(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data or "changeme123",
            role_ids=form.roles.data,
            create_membership=form.create_membership.data,
            qualification=form.qualification.data if hasattr(form, "qualification") else "none",
        )
        if result.success:
            flash(request, "success", f"Member {form.name.data} created successfully!")
            member_id = result.data.id if result.data else None
            if member_id:
                return RedirectResponse(url=f"/admin/members/{member_id}", status_code=303)
            return RedirectResponse(url="/admin/members", status_code=303)
        flash(request, "error", result.message)
        return render(request, "admin/create_member.html", {"form": form}, user=user, db=db)
    flash_form_errors(request, form)
    return render(request, "admin/create_member.html", {"form": form}, user=user, db=db, status_code=422)


@router.get("/members/{user_id}", name="admin.member_detail", dependencies=[require_perms("members.read")])
async def member_detail(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    return render(request, "admin/member_detail.html", {"member": member}, user=user, db=db)


@router.get("/members/{user_id}/edit", name="admin.edit_member", dependencies=[require_perms("members.update")])
async def edit_member_page(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = EditMemberForm(obj=member)
    if member.membership:
        form.membership_start_date.data = member.membership.start_date
        form.membership_expiry_date.data = member.membership.expiry_date
        form.membership_initial_credits.data = member.membership.initial_credits
        form.membership_purchased_credits.data = member.membership.purchased_credits
    form.roles.choices = _role_choices()
    form.roles.data = [r.id for r in member.roles]
    return render(request, "admin/edit_member.html", {"member": member, "form": form}, user=user, db=db)


@router.post("/members/{user_id}/edit", name="admin.edit_member_post", dependencies=[require_perms("members.update")])
async def edit_member_store(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = EditMemberForm(formdata=form_data, obj=member)
    form.roles.choices = _role_choices()
    if form.validate():
        result = UserService.update_member(
            user=member,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            qualification=form.qualification.data,
            qualification_detail=form.qualification_detail.data or None,
            role_ids=form.roles.data,
            is_active=form.is_active.data,
            password=form.password.data or None,
            membership_start_date=form.membership_start_date.data,
            membership_expiry_date=form.membership_expiry_date.data,
            membership_initial_credits=form.membership_initial_credits.data,
            membership_purchased_credits=form.membership_purchased_credits.data,
        )
        flash(request, "success" if result.success else "error", result.message)
        if result.success:
            return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    flash_form_errors(request, form)
    return render(request, "admin/edit_member.html", {"member": member, "form": form}, user=user, db=db, status_code=422)


@router.post("/members/{user_id}/activate", name="admin.activate_user", dependencies=[require_perms("members.activate_account")])
async def activate_user(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    result = UserService.activate_account(user_id)
    flash(request, "success" if result.success else ("warning" if "already active" in result.message else "error"), result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/renew",
    name="admin.renew_membership",
    dependencies=[require_perms("members.manage_membership")],
)
async def renew_membership(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    result = MembershipService.renew_membership(member)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/create",
    name="admin.create_membership",
    dependencies=[require_perms("members.manage_membership")],
)
async def create_membership(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    result = MembershipService.create_membership(member)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/membership/activate",
    name="admin.activate_membership",
    dependencies=[require_perms("members.manage_membership")],
)
async def activate_membership(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    result = MembershipService.activate_membership(member)
    if not result.success:
        flash(request, "error", result.message)
        return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    payment = PaymentService.get_completed_membership_payment(user_id)
    try:
        if payment:
            membership_activated.send(user_id=member.id, payment_id=payment.id)
            flash(request, "success", f"Membership activated for {member.name}! Receipt email sent.")
        else:
            flash(request, "success", f"Membership activated for {member.name}!")
    except Exception:
        flash(request, "success", f"Membership activated for {member.name}!")
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)


@router.post(
    "/members/{user_id}/credits/adjust",
    name="admin.adjust_credits",
    dependencies=[require_perms("members.manage_membership")],
)
async def adjust_credits(user_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    member = UserService.get_user_by_id(user_id)
    if not member:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    if not member.membership:
        flash(request, "error", "Member does not have a membership.")
        return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    try:
        quantity = int(form_data.get("quantity", 0))
        action = form_data.get("action", "add")
    except ValueError:
        flash(request, "error", "Please enter a valid number of credits.")
        return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)
    reason = (form_data.get("reason") or "").strip() or "Admin adjustment"
    result = UserService.adjust_member_credits(
        member,
        admin_user_id=user.id,
        quantity=quantity,
        action=action,
        reason=reason,
    )
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=f"/admin/members/{user_id}", status_code=303)

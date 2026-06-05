from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, require_perms, verify_csrf
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import RoleForm
from app.schemas.form_helpers import FormView, parse_form
from app.services import rbac
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.roles"])


def _permission_choices():
    return [(permission.id, permission.name) for permission in rbac.list_permissions()]


def _role_form_view(role=None, *, values: dict | None = None, errors: dict | None = None) -> FormView:
    if values is None and role is not None:
        values = {
            "name": role.name,
            "description": role.description or "",
            "permissions": [permission.id for permission in role.permissions],
        }
    return FormView(values=values or {}, errors=errors, choices={"permissions": _permission_choices()})


@router.get("/roles", name="admin.roles_index", dependencies=[require_perms("roles.manage")])
async def roles_index(request: Request, user: CurrentUser):
    roles = rbac.list_roles()
    permissions = rbac.list_permissions()
    return render(request, "admin/roles.html", {"roles": roles, "permissions": permissions}, user=user)


@router.get("/roles/create", name="admin.create_role", dependencies=[require_perms("roles.manage")])
async def create_role_page(request: Request, user: CurrentUser):
    form = _role_form_view()
    return render(request, "admin/role_form.html", {"form": form, "role": None, "mode": "create"}, user=user)


@router.post("/roles/create", name="admin.create_role_post", dependencies=[require_perms("roles.manage")])
async def create_role_store(request: Request, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    parsed, errors, values = parse_form(RoleForm, form_data)
    form = _role_form_view(values=values, errors=errors)
    if parsed:
        result = rbac.create_role(parsed.name, parsed.description, parsed.permissions)
        if result.success:
            flash(request, "success", "Role created!")
            return RedirectResponse(url="/admin/roles", status_code=303)
        flash(request, "error", result.message)
        return render(request, "admin/role_form.html", {"form": form, "role": None}, user=user)
    flash_form_errors(request, errors)
    return render(request, "admin/role_form.html", {"form": form, "role": None}, user=user, status_code=422)


@router.get("/roles/{role_id}/edit", name="admin.edit_role", dependencies=[require_perms("roles.manage")])
async def edit_role_page(role_id: int, request: Request, user: CurrentUser):
    role = rbac.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, status_code=404)
    form = _role_form_view(role=role)
    return render(request, "admin/role_form.html", {"form": form, "role": role, "mode": "edit"}, user=user)


@router.post("/roles/{role_id}/edit", name="admin.edit_role_post", dependencies=[require_perms("roles.manage")])
async def edit_role_store(role_id: int, request: Request, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    role = rbac.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, status_code=404)
    parsed, errors, values = parse_form(RoleForm, form_data)
    form = _role_form_view(values=values, errors=errors)
    if parsed:
        result = rbac.update_role(role, parsed.name, parsed.description, parsed.permissions)
        if result.success:
            flash(request, "success", result.message or "Role updated!")
            return RedirectResponse(url="/admin/roles", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, errors)
    return render(request, "admin/role_form.html", {"form": form, "role": role}, user=user, status_code=422)


@router.post("/roles/{role_id}/delete", name="admin.delete_role", dependencies=[require_perms("roles.manage")])
async def delete_role(role_id: int, request: Request, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    role = rbac.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, status_code=404)
    result = rbac.delete_role(role)
    flash(
        request,
        "success" if result.success else "error",
        result.message or ("Role deleted." if result.success else "Error deleting role."),
    )
    return RedirectResponse(url="/admin/roles", status_code=303)

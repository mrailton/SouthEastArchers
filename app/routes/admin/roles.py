from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.forms.admin_forms import RoleForm
from app.routes.admin._helpers import flash_form_errors
from app.services.rbac_service import RBACService
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.roles"])


@router.get("/roles", name="admin.roles_index", dependencies=[require_perms("roles.manage")])
async def roles_index(request: Request, db: DbSession, user: CurrentUser):
    roles = RBACService.list_roles()
    permissions = RBACService.list_permissions()
    return render(request, "admin/roles.html", {"roles": roles, "permissions": permissions}, user=user, db=db)


@router.get("/roles/create", name="admin.create_role", dependencies=[require_perms("roles.manage")])
async def create_role_page(request: Request, db: DbSession, user: CurrentUser):
    form = RoleForm()
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    return render(request, "admin/role_form.html", {"form": form, "role": None, "mode": "create"}, user=user, db=db)


@router.post("/roles/create", name="admin.create_role_post", dependencies=[require_perms("roles.manage")])
async def create_role_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = RoleForm(formdata=form_data)
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    if form.validate():
        result = RBACService.create_role(form.name.data, form.description.data, form.permissions.data or [])
        if result.success:
            flash(request, "success", "Role created!")
            return RedirectResponse(url="/admin/roles", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/role_form.html", {"form": form, "role": None}, user=user, db=db, status_code=422)


@router.get("/roles/{role_id}/edit", name="admin.edit_role", dependencies=[require_perms("roles.manage")])
async def edit_role_page(role_id: int, request: Request, db: DbSession, user: CurrentUser):
    role = RBACService.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = RoleForm(obj=role)
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    form.permissions.data = [p.id for p in role.permissions]
    return render(request, "admin/role_form.html", {"form": form, "role": role, "mode": "edit"}, user=user, db=db)


@router.post("/roles/{role_id}/edit", name="admin.edit_role_post", dependencies=[require_perms("roles.manage")])
async def edit_role_store(role_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    role = RBACService.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = RoleForm(formdata=form_data, obj=role)
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    if form.validate():
        result = RBACService.update_role(role, form.name.data, form.description.data, form.permissions.data or [])
        if result.success:
            flash(request, "success", result.message or "Role updated!")
            return RedirectResponse(url="/admin/roles", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/role_form.html", {"form": form, "role": role}, user=user, db=db, status_code=422)


@router.post("/roles/{role_id}/delete", name="admin.delete_role", dependencies=[require_perms("roles.manage")])
async def delete_role(role_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    role = RBACService.get_role(role_id)
    if not role:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    result = RBACService.delete_role(role)
    flash(
        request,
        "success" if result.success else "error",
        result.message or ("Role deleted." if result.success else "Error deleting role."),
    )
    return RedirectResponse(url="/admin/roles", status_code=303)

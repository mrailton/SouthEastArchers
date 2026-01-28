from collections.abc import Sequence
from typing import cast

from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import RoleForm
from app.services.rbac_service import RBACService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/roles")
@permission_required("roles.manage")
def roles_index():
    roles = RBACService.list_roles()
    permissions = RBACService.list_permissions()
    return render_template("admin/roles.html", roles=roles, permissions=permissions)


@bp.get("/roles/create")
@permission_required("roles.manage")
def create_role():
    form = RoleForm()
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    return render_template("admin/role_form.html", form=form, mode="create")


@bp.post("/roles/create")
@permission_required("roles.manage")
def create_role_post():
    form = RoleForm()
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    if form.validate_on_submit():
        role, error = RBACService.create_role(
            name=form.name.data.strip(),
            description=form.description.data,
            permission_ids=form.permissions.data or [],
        )
        if error:
            flash(error, "error")
            return render_template("admin/role_form.html", form=form, mode="create")
        flash("Role created successfully.", "success")
        return redirect(url_for("admin.roles_index"))

    for field, errors in form.errors.items():
        for err in errors:
            flash(err, "error")
    return render_template("admin/role_form.html", form=form, mode="create")


@bp.get("/roles/<int:role_id>/edit")
@permission_required("roles.manage")
def edit_role(role_id: int):
    role = RBACService.get_role(role_id)
    if not role:
        flash("Role not found.", "error")
        return redirect(url_for("admin.roles_index"))

    form = RoleForm(obj=role)
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    form.permissions.data = [p.id for p in cast(Sequence, role.permissions)]
    return render_template("admin/role_form.html", form=form, mode="edit", role=role)


@bp.post("/roles/<int:role_id>/edit")
@permission_required("roles.manage")
def edit_role_post(role_id: int):
    role = RBACService.get_role(role_id)
    if not role:
        flash("Role not found.", "error")
        return redirect(url_for("admin.roles_index"))

    form = RoleForm()
    form.permissions.choices = [(p.id, p.name) for p in RBACService.list_permissions()]
    if form.validate_on_submit():
        success, message = RBACService.update_role(
            role=role,
            name=form.name.data.strip(),
            description=form.description.data,
            permission_ids=form.permissions.data or [],
        )
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.roles_index"))

    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(err, "error")

    return render_template("admin/role_form.html", form=form, mode="edit", role=role)


@bp.post("/roles/<int:role_id>/delete")
@permission_required("roles.manage")
def delete_role(role_id: int):
    role = RBACService.get_role(role_id)
    if not role:
        flash("Role not found.", "error")
        return redirect(url_for("admin.roles_index"))

    success, message = RBACService.delete_role(role)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.roles_index"))

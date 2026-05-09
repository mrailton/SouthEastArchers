from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import RoleForm
from app.services.rbac_service import RBACService
from app.utils import permission_required


class EditRoleController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self, role_id: int):
        role = self.service.get_role(role_id)
        if not role:
            flash("Role not found.", "error")
            return redirect(url_for("admin.roles_index"))

        form = RoleForm(obj=role)
        form.permissions.choices = [(p.id, p.name) for p in self.service.list_permissions()]
        form.permissions.data = [p.id for p in role.permissions]
        return render_template("admin/role_form.html", form=form, mode="edit", role=role)

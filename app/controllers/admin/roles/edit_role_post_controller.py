from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import RoleForm
from app.services.rbac_service import RBACService
from app.utils import permission_required


class EditRolePostController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self, role_id: int):
        role = self.service.get_role(role_id)
        if not role:
            flash("Role not found.", "error")
            return redirect(url_for("admin.roles_index"))

        form = RoleForm()
        form.permissions.choices = [(p.id, p.name) for p in self.service.list_permissions()]
        if form.validate_on_submit():
            result = self.service.update_role(
                role=role,
                name=form.name.data.strip(),
                description=form.description.data,
                permission_ids=form.permissions.data or [],
            )
            flash(result.message, "success" if result.success else "error")
            if result.success:
                return redirect(url_for("admin.roles_index"))

        else:
            for field, errors in form.errors.items():
                for err in errors:
                    flash(err, "error")

        return render_template("admin/role_form.html", form=form, mode="edit", role=role)

from flask import flash, redirect, render_template, url_for

from app.forms.admin_forms import RoleForm
from app.services.rbac_service import RBACService
from app.utils import permission_required


class CreateRolePostController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self):
        form = RoleForm()
        form.permissions.choices = [(p.id, p.name) for p in self.service.list_permissions()]
        if form.validate_on_submit():
            result = self.service.create_role(
                name=form.name.data.strip(),
                description=form.description.data,
                permission_ids=form.permissions.data or [],
            )
            if not result.success:
                flash(result.message, "error")
                return render_template("admin/role_form.html", form=form, mode="create")
            flash("Role created successfully.", "success")
            return redirect(url_for("admin.roles_index"))

        for field, errors in form.errors.items():
            for err in errors:
                flash(err, "error")
        return render_template("admin/role_form.html", form=form, mode="create")

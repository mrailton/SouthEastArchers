from flask import render_template

from app.forms.admin_forms import RoleForm
from app.services.rbac_service import RBACService
from app.utils import permission_required


class CreateRoleController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self):
        form = RoleForm()
        form.permissions.choices = [(p.id, p.name) for p in self.service.list_permissions()]
        return render_template("admin/role_form.html", form=form, mode="create")

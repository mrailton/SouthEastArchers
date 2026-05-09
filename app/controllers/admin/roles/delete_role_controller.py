from flask import flash, redirect, url_for

from app.services.rbac_service import RBACService
from app.utils import permission_required


class DeleteRoleController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self, role_id: int):
        role = self.service.get_role(role_id)
        if not role:
            flash("Role not found.", "error")
            return redirect(url_for("admin.roles_index"))

        result = self.service.delete_role(role)
        flash(result.message, "success" if result.success else "error")
        return redirect(url_for("admin.roles_index"))

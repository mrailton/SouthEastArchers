from flask import render_template

from app.services.rbac_service import RBACService
from app.utils import permission_required


class RolesIndexController:
    def __init__(self):
        super().__init__()
        self.service = RBACService

    @permission_required("roles.manage")
    def __call__(self):
        roles = self.service.list_roles()
        permissions = self.service.list_permissions()
        return render_template("admin/roles.html", roles=roles, permissions=permissions)

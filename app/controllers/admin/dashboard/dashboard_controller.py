from flask import render_template

from app.services import AdminService
from app.utils.decorators import permission_required


class DashboardController:
    def __init__(self):
        super().__init__()
        self.service = AdminService

    @permission_required("admin.dashboard.view")
    def __call__(self):
        result = self.service.get_dashboard_stats()
        assert result.data is not None
        return render_template("admin/dashboard.html", **result.data)

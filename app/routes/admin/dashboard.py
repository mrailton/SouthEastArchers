from flask import render_template

from app.services import AdminService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/dashboard")
@permission_required("admin.dashboard.view")
def dashboard():
    result = AdminService.get_dashboard_stats()
    assert result.data is not None
    return render_template("admin/dashboard.html", **result.data)

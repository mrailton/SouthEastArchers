from flask import render_template

from app.services import AdminService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/dashboard")
@permission_required("admin.dashboard.view")
def dashboard():
    stats = AdminService.get_dashboard_stats()
    return render_template("admin/dashboard.html", **stats)

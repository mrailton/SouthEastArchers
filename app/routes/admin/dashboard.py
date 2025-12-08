from flask import render_template

from app.services import AdminService

from . import admin_required, bp


@bp.route("/dashboard")
@admin_required
def dashboard():
    stats = AdminService.get_dashboard_stats()
    return render_template("admin/dashboard.html", **stats)
